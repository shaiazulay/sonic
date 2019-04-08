from __future__ import print_function, with_statement

import logging
import os

from collections import OrderedDict, namedtuple

from ..core.config import Config
from ..core.driver import KernelDriver
from ..core.inventory import Interrupt, PowerCycle, Watchdog, Xcvr, Reset
from ..core.types import I2cAddr
from ..core.utils import FileWaiter, MmapResource, inSimulation, simulateWith, \
                         writeConfig

from ..drivers.i2c import I2cKernelDriver
from ..drivers.scd import ScdKernelDriver
from ..drivers.sysfs import SysfsDriver
from ..drivers.accessors import PsuImpl, ResetImpl, XcvrImpl

from .common import PciComponent, I2cComponent

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

class Scd(PciComponent):
   BusTweak = namedtuple('BusTweak', 'addr, t, datr, datw, ed')
   def __init__(self, addr, drivers=None, **kwargs):
      drivers = drivers or [KernelDriver(module='scd'),
                            ScdKernelDriver(scd=self, addr=addr),
                            SysfsDriver(sysfsPath=addr.getSysfsPath())]
      super(Scd, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.pciSysfs = self.addr.getSysfsPath()
      self.masters = OrderedDict()
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
      self.msiRearmOffset = None

   def setMsiRearmOffset(self, offset):
      self.msiRearmOffset = offset

   def createPowerCycle(self, reg=0x7000, wr=0xDEAD):
      powerCycle = ScdPowerCycle(self, reg=reg, wr=wr)
      self.powerCycles.append(powerCycle)
      return powerCycle

   def getPowerCycles(self):
      return self.powerCycles

   def createWatchdog(self, reg=0x0120):
      return ScdWatchdog(self, reg=reg)

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

   def i2cAddr(self, bus, addr):
      return ScdI2cAddr(self, bus, addr)

   def getInterrupts(self):
      return self.interrupts

   def addBusTweak(self, addr, t=1, datr=1, datw=3, ed=0):
      addr = self.i2cAddr(addr.bus, addr.address)
      self.tweaks.append(Scd.BusTweak(addr, t, datr, datw, ed))

   def addSmbusMaster(self, addr, mid, bus=8):
      self.masters[addr] = {
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

   def addLeds(self, leds):
      self.leds += leds

   def addReset(self, gpio):
      scdReset = ScdReset(self.pciSysfs, gpio)
      self.resets += [scdReset]
      return scdReset

   def addResets(self, gpios):
      scdResets = [ScdReset(self.pciSysfs, gpio) for gpio in gpios]
      self.resets += scdResets
      return {reset.getName(): reset for reset in scdResets}

   def addGpio(self, gpio):
      self.gpios += [gpio]

   def addGpios(self, gpios):
      self.gpios += gpios

   def _addXcvr(self, xcvrId, xcvrType, bus, interruptLine):
      addr = self.i2cAddr(bus, Xcvr.ADDR)
      reset = None
      if xcvrType != Xcvr.SFP:
         reset = ResetImpl(name='%s%s' % (Xcvr.typeStr(xcvrType), xcvrId),
                           driver=self.drivers['SysfsDriver'])
      xcvr = XcvrImpl(xcvrId=xcvrId, xcvrType=xcvrType,
                      driver=self.drivers['SysfsDriver'],
                      addr=addr, interruptLine=interruptLine,
                      reset=reset)
      self.addComponent(I2cComponent(addr=addr,
                           drivers=[I2cKernelDriver(name='sff8436', addr=addr)]))
      self.addBusTweak(addr)
      self.xcvrs.append(xcvr)
      return xcvr

   def addOsfp(self, addr, xcvrId, bus, interruptLine=None):
      self.osfps += [(addr, xcvrId)]
      return self._addXcvr(xcvrId, Xcvr.OSFP, bus, interruptLine)

   def addQsfp(self, addr, xcvrId, bus, interruptLine=None):
      self.qsfps += [(addr, xcvrId)]
      return self._addXcvr(xcvrId, Xcvr.QSFP, bus, interruptLine)

   def addSfp(self, addr, xcvrId, bus, interruptLine=None):
      self.sfps += [(addr, xcvrId)]
      return self._addXcvr(xcvrId, Xcvr.SFP, bus, interruptLine)

   # In platforms, should change "statusGpios" to "statusGpio" and make it a boolean
   def createPsu(self, psuId, statusGpios=True, **kwargs):
      return PsuImpl(psuId=psuId, driver=self.drivers['SysfsDriver'],
                     statusGpio=statusGpios, **kwargs)

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

   def getUio(self, reg, bit):
      if not self.uioMap:
         self.uioMapInit()
      return '/dev/%s' % self.uioMap[
            'uio-%s-%d-%d' % (getattr(self, 'addr'), reg, bit)]
