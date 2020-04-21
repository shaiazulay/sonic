from __future__ import print_function, with_statement

import os

from collections import OrderedDict, namedtuple

from ..accessors.led import LedImpl
from ..accessors.psu import PsuImpl
from ..accessors.reset import ResetImpl
from ..accessors.xcvr import XcvrImpl

from ..core.config import Config
from ..core.driver import KernelDriver
from ..core.types import I2cAddr, MdioClause, MdioSpeed
from ..core.utils import FileWaiter, MmapResource, simulateWith, writeConfig
from ..core.log import getLogger

from ..drivers.i2c import I2cKernelDriver
from ..drivers.scd import ScdKernelDriver
from ..drivers.sysfs import (
   LedSysfsDriver,
   PsuSysfsDriver,
   ResetSysfsDriver,
   XcvrSysfsDriver,
)

from ..inventory.interrupt import Interrupt
from ..inventory.powercycle import PowerCycle
from ..inventory.watchdog import Watchdog
from ..inventory.xcvr import Xcvr
from ..inventory.reset import Reset

from .common import PciComponent, I2cComponent

logging = getLogger(__name__)

SYS_UIO_PATH = '/sys/class/uio'

class ScdI2cAddr(I2cAddr):
   def __init__(self, scd, bus, addr):
      super(ScdI2cAddr, self).__init__(bus, addr)
      self.scd_ = scd

   @property
   def bus(self):
      return self.scd_.i2cOffset + self.bus_

class ScdReset(Reset):
   def __init__(self, path, reset):
      self.addr = reset.addr
      self.name = reset.name
      self.bit = reset.bit
      self.path = os.path.join(path, self.name)

   def read(self):
      with open(self.path, 'r') as f:
         return f.read().rstrip()

   def resetSim(self, value):
      logging.debug('resetting device %s', self.name)

   @simulateWith(resetSim)
   def doReset(self, value):
      with open(self.path, 'w') as f:
         f.write('1' if value else '0')

   def resetIn(self):
      self.doReset(True)

   def resetOut(self):
      self.doReset(False)

   def getName(self):
      return self.name

class ScdWatchdog(Watchdog):
   def __init__(self, scd, reg=0x0120):
      self.scd = scd
      self.reg = reg

   @staticmethod
   def armReg(timeout):
      regValue = 0
      if timeout > 0:
         # Set enable bit
         regValue |= 1 << 31
         # Powercycle
         regValue |= 2 << 29
         # Timeout value
         regValue |= timeout
      return regValue

   def armSim(self, timeout):
      regValue = self.armReg(timeout)
      logging.info("watchdog arm reg={0:32b}".format(regValue))
      return True

   @simulateWith(armSim)
   def arm(self, timeout):
      regValue = self.armReg(timeout)
      try:
         with self.scd.getMmap() as mmap:
            logging.info('arm reg = {0:32b}'.format(regValue))
            mmap.write32(self.reg, regValue)
      except RuntimeError as e:
         logging.error("watchdog arm/stop error: {}".format(e))
         return False
      return True

   def stopSim(self):
      logging.info("watchdog stop")
      return True

   @simulateWith(stopSim)
   def stop(self):
      return self.arm(0)

   def statusSim(self):
      logging.info("watchdog status")
      return { "enabled": True, "timeout": 300 }

   @simulateWith(statusSim)
   def status(self):
      try:
         with self.scd.getMmap() as mmap:
            regValue = mmap.read32(self.reg)
            enabled = bool(regValue >> 31)
            timeout = regValue & ((1<<16)-1)
         return { "enabled": enabled, "timeout": timeout }
      except RuntimeError as e:
         logging.error("watchdog status error: {}".format(e))
         return None

class ScdPowerCycle(PowerCycle):
   def __init__(self, scd, reg=0x7000, wr=0xDEAD):
      self.scd = scd
      self.reg = reg
      self.wr = wr

   def powerCycle(self):
      logging.info("Initiating powercycle through SCD")
      try:
         with self.scd.getMmap() as mmap:
            mmap.write32(self.reg, self.wr)
            logging.info("Powercycle triggered by SCD")
            return True
      except RuntimeError as e:
         logging.error("powercycle error: %s", e)
         return False

class ScdInterrupt(Interrupt):
   def __init__(self, reg, bit):
      self.reg = reg
      self.bit = bit

   def set(self):
      self.reg.setMask(self.bit)

   def clear(self):
      self.reg.clearMask(self.bit)

   def getFile(self):
      return self.reg.scd.getUio(self.reg.num, self.bit)

class ScdInterruptRegister(object):
   def __init__(self, scd, addr, num, mask):
      self.scd = scd
      self.num = num
      self.readAddr = addr
      self.setAddr = addr
      self.clearAddr = addr + 0x10
      self.statusAddr = addr + 0x20
      self.mask = mask

   def setReg(self, reg, wr):
      try:
         with self.scd.getMmap() as mmap:
            mmap.write32(reg, wr)
            return True
      except RuntimeError as e:
         logging.error("write register %s with %s: %s", reg, wr, e)
         return False

   def readReg(self, reg):
      try:
         with self.scd.getMmap() as mmap:
            res = mmap.read32(reg)
            return hex(res)
      except RuntimeError as e:
         logging.error("read register %s: %s", reg, e)
         return None

   def setMask(self, bit):
      mask = 0 | 1 << bit
      res = self.readReg(self.setAddr)
      if res is not None:
         self.setReg(self.setAddr, (mask | int(res, 16)) & 0xffffffff)

   def clearMask(self, bit):
      mask = 0 | 1 << bit
      res = self.readReg(self.setAddr)
      if res is not None:
         self.setReg(self.clearAddr, (mask | ~int(res, 16)) & 0xffffffff)

   def setup(self):
      if not Config().init_irq:
         return
      writeConfig(self.scd.pciSysfs, OrderedDict([
         ('interrupt_mask_read_offset%s' % self.num, str(self.readAddr)),
         ('interrupt_mask_set_offset%s' % self.num, str(self.setAddr)),
         ('interrupt_mask_clear_offset%s' % self.num, str(self.clearAddr)),
         ('interrupt_status_offset%s' % self.num, str(self.statusAddr)),
         ('interrupt_mask%s' % self.num, str(self.mask)),
      ]))

   def getInterruptBit(self, bit):
      return ScdInterrupt(self, bit) if Config().init_irq else None

class ScdMdio(object):
   def __init__(self, scd, master, bus, devIdx, port, device, clause, name):
      self.scd = scd
      self.master = master
      self.bus = bus
      self.id = devIdx
      self.portAddr = port
      self.deviceAddr = device
      self.clause = clause
      self.name = name

class ScdSmbus(object):
   def __init__(self, scd, bus):
      self.scd = scd
      self.bus = bus

   def i2cAddr(self, addr):
      return self.scd.i2cAddr(self.bus, addr)

class Scd(PciComponent):
   BusTweak = namedtuple('BusTweak', 'addr, t, datr, datw, ed')
   def __init__(self, addr, drivers=None, registerCls=None, **kwargs):
      self.pciSysfs = addr.getSysfsPath()
      drivers = drivers or [KernelDriver(module='scd'),
                            ScdKernelDriver(scd=self, addr=addr,
                                            registerCls=registerCls),
                            LedSysfsDriver(sysfsPath=os.path.join(self.pciSysfs,
                                                                  'leds')),
                            PsuSysfsDriver(sysfsPath=self.pciSysfs),
                            ResetSysfsDriver(sysfsPath=self.pciSysfs),
                            XcvrSysfsDriver(sysfsPath=self.pciSysfs)]
      self.smbusMasters = OrderedDict()
      self.mmapReady = False
      self.interrupts = []
      self.fanGroups = []
      self.leds = []
      self.gpios = []
      self.powerCycles = []
      self.osfps = []
      self.qsfps = []
      self.sfps = []
      self.tweaks = []
      self.xcvrs = []
      self.uioMap = {}
      self.resets = []
      self.i2cOffset = 0
      self.mdioMasters = {}
      self.mdios = []
      self.msiRearmOffset = None
      super(Scd, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.regs = self.drivers['scd-hwmon'].regs

   def __str__(self):
      return '%s()' % self.__class__.__name__

   def setMsiRearmOffset(self, offset):
      self.msiRearmOffset = offset

   def createPowerCycle(self, reg=0x7000, wr=0xDEAD):
      powerCycle = ScdPowerCycle(self, reg=reg, wr=wr)
      self.powerCycles.append(powerCycle)
      self.inventory.addPowerCycle(powerCycle)
      return powerCycle

   def getPowerCycles(self):
      return self.powerCycles

   def createWatchdog(self, reg=0x0120):
      watchdog = ScdWatchdog(self, reg=reg)
      self.inventory.addWatchdog(watchdog)
      return watchdog

   def createInterrupt(self, addr, num, mask=0xffffffff):
      interrupt = ScdInterruptRegister(self, addr, num, mask)
      self.interrupts.append(interrupt)
      return interrupt

   def getMmap(self):
      path = os.path.join(self.pciSysfs, "resource0")
      if not self.mmapReady:
         # check that the scd driver is loaded the first time
         drv = self.drivers['scd']
         if not drv.loaded():
            # This codepath is unlikely to be used
            drv.setup()
            FileWaiter(path, 5).waitFileReady()
         self.mmapReady = True
      return MmapResource(path)

   def i2cAddr(self, bus, addr, t=1, datr=3, datw=3, ed=0):
      addr = ScdI2cAddr(self, bus, addr)
      self.tweaks.append(Scd.BusTweak(addr, t, datr, datw, ed))
      return addr

   def getSmbus(self, bus):
      return ScdSmbus(self, bus)

   def getInterrupts(self):
      return self.interrupts

   def addBusTweak(self, addr, t=1, datr=3, datw=3, ed=0):
      self.i2cAddr(addr.bus, addr.address, t=t, datr=datr, datw=datw, ed=ed )

   def addSmbusMaster(self, addr, mid, bus=8):
      self.smbusMasters[addr] = {
         'id': mid,
         'bus': bus,
      }

   def addSmbusMasterRange(self, addr, count, spacing=0x100, bus=8):
      addrs = range(addr, addr + (count + 1) * spacing, spacing)
      for i, addr in enumerate(addrs, 0):
         self.addSmbusMaster(addr, i, bus)

   def addFanGroup(self, addr, platform, num):
      self.fanGroups += [(addr, platform, num)]

   def addLed(self, addr, name):
      self.leds += [(addr, name)]
      return LedImpl(name=name, driver=self.drivers['LedSysfsDriver'])

   def addLeds(self, leds):
      return [self.addLed(*led) for led in leds]

   def addReset(self, gpio):
      scdReset = ScdReset(self.pciSysfs, gpio)
      self.resets += [scdReset]
      self.inventory.addReset(scdReset)
      return scdReset

   def addResets(self, gpios):
      scdResets = [ScdReset(self.pciSysfs, gpio) for gpio in gpios]
      self.resets += scdResets
      resetDict = {reset.getName(): reset for reset in scdResets}
      self.inventory.addResets(resetDict)
      return resetDict

   def addGpio(self, gpio):
      self.gpios += [gpio]

   def addGpios(self, gpios):
      self.gpios += gpios

   def _addXcvr(self, xcvrId, xcvrType, bus, interruptLine, leds=None, drvName=None):
      addr = self.i2cAddr(bus, Xcvr.ADDR, t=1, datr=0, datw=3, ed=0)
      reset = None
      if xcvrType != Xcvr.SFP:
         reset = ResetImpl(name='%s%s' % (Xcvr.typeStr(xcvrType), xcvrId),
                           driver=self.drivers['ResetSysfsDriver'])
      xcvr = XcvrImpl(xcvrId=xcvrId, xcvrType=xcvrType,
                      driver=self.drivers['XcvrSysfsDriver'],
                      addr=addr, interruptLine=interruptLine,
                      reset=reset, leds=leds)
      self.newComponent(I2cComponent, addr=addr,
                        drivers=[I2cKernelDriver(name=drvName, addr=addr)])
      self.xcvrs.append(xcvr)
      self.inventory.addXcvr(xcvr)
      return xcvr

   def addOsfp(self, addr, xcvrId, bus, interruptLine=None, leds=None):
      self.osfps += [(addr, xcvrId)]
      return self._addXcvr(xcvrId, Xcvr.OSFP, bus, interruptLine, leds=leds,
                           drvName='optoe1')

   def addQsfp(self, addr, xcvrId, bus, interruptLine=None, leds=None):
      self.qsfps += [(addr, xcvrId)]
      return self._addXcvr(xcvrId, Xcvr.QSFP, bus, interruptLine, leds=leds,
                           drvName='optoe1')

   def addSfp(self, addr, xcvrId, bus, interruptLine=None, leds=None):
      self.sfps += [(addr, xcvrId)]
      return self._addXcvr(xcvrId, Xcvr.SFP, bus, interruptLine, leds=leds,
                           drvName='optoe2')

   # In platforms, should change "statusGpios" to "statusGpio" and make it a boolean
   def createPsu(self, psuId, driver='PsuSysfsDriver', statusGpios=True, led=None,
                 **kwargs):
      psu = PsuImpl(psuId=psuId, driver=self.drivers[driver],
                     statusGpio=statusGpios, led=led, **kwargs)
      self.inventory.addPsus([psu])
      return psu

   def addMdioMaster(self, addr, masterId, busCount=1, speed=MdioSpeed.S2_5):
      self.mdioMasters[addr] = {
         'id': masterId,
         'bus': busCount,
         'speed': speed,
         'devCount': [0] * busCount,
      }

   def addMdioMasterRange(self, base, count, spacing=0x40, busCount=1):
      addrs = range(base, base + count * spacing, spacing)
      for i, addr in enumerate(addrs, 0):
         self.addMdioMaster(addr, i, busCount)

   def addMdio(self, master, portAddr, bus=0, devAddr=1, clause=MdioClause.C45):
      addrs = [k for k, v in self.mdioMasters.items() if v['id'] == master]
      assert len(addrs) == 1, 'Mdio bus cannot be determined'
      assert bus < self.mdioMasters[addrs[0]]['bus'], 'Bus number is too large'

      devIndex = self.mdioMasters[addrs[0]]['devCount'][bus]
      self.mdioMasters[addrs[0]]['devCount'][bus] += 1
      name = "mdio{}_{}_{}".format(master, bus, devIndex)
      mdio = ScdMdio(self, master, bus, devIndex, portAddr, devAddr, clause, name)
      self.mdios.append(mdio)
      return mdio

   def allGpios(self):
      def zipXcvr(xcvrType, gpio_names, entries):
         res = []
         for data in entries.values():
            for name, gpio in zip(gpio_names, data['gpios']):
               res += [ ("%s%d_%s" % (xcvrType, data['id'], name), gpio.ro) ]
         return res

      sfp_names = [
         "rxlos", "txfault", "present", "rxlos_changed", "txfault_changed",
         "present_changed", "txdisable", "rate_select0", "rate_select1",
      ]

      qsfp_names = [
         "interrupt", "present", "interrupt_changed", "present_changed",
         "lp_mode", "reset", "modsel",
      ]

      osfp_names = [
         "interrupt", "present", "interrupt_changed", "present_changed",
         "lp_mode", "reset", "modsel",
      ]

      gpios = []
      gpios += zipXcvr("sfp", sfp_names, self.sfps)
      gpios += zipXcvr("qsfp", qsfp_names, self.qsfps)
      gpios += zipXcvr("osfp", osfp_names, self.osfps)
      gpios += [ (gpio.name, gpio.ro) for gpio in self.gpios ]
      gpios += [ (reset.name, False) for reset in self.resets ]

      return gpios

   def getSysfsResetNameList(self, xcvrs=True):
      entries = [reset.name for reset in self.resets]
      if xcvrs:
         entries += ['qsfp%d_reset' % xcvrId for _, xcvrId in self.qsfps]
         entries += ['osfp%d_reset' % xcvrId for _, xcvrId in self.osfps]
      return entries

   def resetOut(self):
      super(Scd, self).resetOut()
      for xcvr in self.xcvrs:
         xcvr.setModuleSelect(True)
         xcvr.setTxDisable(False)

   def uioMapInit(self):
      for uio in os.listdir(SYS_UIO_PATH):
         with open(os.path.join(SYS_UIO_PATH, uio, 'name')) as uioName:
            self.uioMap[uioName.read().strip()] = uio

   def simGetUio(self, reg, bit):
      return '/dev/uio-%s-%x-%d' % (self.addr, reg, bit)

   @simulateWith(simGetUio)
   def getUio(self, reg, bit):
      if not self.uioMap:
         self.uioMapInit()
      return '/dev/%s' % self.uioMap[
            'uio-%s-%x-%d' % (getattr(self, 'addr'), reg, bit)]
