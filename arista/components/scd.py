from __future__ import print_function, with_statement

import logging
import os
import time

from collections import OrderedDict, namedtuple

from ..core.config import Config
from ..core.driver import i2cBusFromName
from ..core.inventory import Interrupt, PowerCycle, Psu, Watchdog, Xcvr, Reset
from ..core.types import I2cAddr, SysfsPath
from ..core.utils import MmapResource, inSimulation, simulateWith, writeConfig

from .common import PciComponent, KernelDriver, PciKernelDriver, I2cKernelComponent

SCD_WAIT_TIMEOUT = 5.
SYS_UIO_PATH = '/sys/class/uio'

class ScdI2cAddr(I2cAddr):
   def __init__(self, scd, bus, addr):
      super(ScdI2cAddr, self).__init__(bus, addr)
      self.scd_ = scd

   @property
   def bus(self):
      return self.scd_.i2cOffset + self.bus_

class ScdSysfsGroup(SysfsPath):
   def __init__(self, objNum, typeStr, sysfsPath):
      self.prefix = '%s%d_' % (typeStr, objNum)
      self.prefixPath = os.path.join(sysfsPath, self.prefix)

class ScdSysfsRW(ScdSysfsGroup):
   def __init__(self, objNum, typeStr, sysfsPath):
      ScdSysfsGroup.__init__(self, objNum, typeStr, sysfsPath)

   def getSysfsGpio(self, name):
      return '%s%s' % (self.prefixPath, name)

   def readValueSim(self, name):
      logging.info('read sysfs %s entry %s', self.prefix, name)
      return "1"

   @simulateWith(readValueSim)
   def readValue(self, name):
      with open(self.getSysfsGpio(name), 'r') as f:
         return f.read().rstrip()

   def writeValueSim(self, name, value):
      logging.info('write sysfs %s entry %s value %s', self.prefix, name, value)
      return True

   @simulateWith(writeValueSim)
   def writeValue(self, name, value):
      with open(self.getSysfsGpio(name), 'w') as f:
         f.write(str(value))
      return True

class ScdKernelXcvr(Xcvr):
   def __init__(self, portNum, xcvrType, addr, sysfsDir, interruptLine=None):
      Xcvr.__init__(self, portNum, xcvrType, addr)
      typeStr = Xcvr.typeStr(xcvrType)
      self.rw = ScdSysfsRW(portNum, typeStr, sysfsDir)
      self.interruptLine = interruptLine
      self.reset = None if xcvrType == Xcvr.SFP else ScdXcvrReset(self, typeStr)

   def getPresence(self):
      return self.rw.readValue('present') == '1'

   def getLowPowerMode(self):
      if self.xcvrType == Xcvr.SFP:
         return False
      return self.rw.readValue('lp_mode') == '1'

   def setLowPowerMode(self, value):
      if self.xcvrType == Xcvr.SFP:
         return False
      return self.rw.writeValue('lp_mode', '1' if value else '0')

   def getModuleSelect(self):
      if self.xcvrType == Xcvr.SFP:
         return True
      return self.rw.readValue('modsel')

   def setModuleSelect(self, value):
      if self.xcvrType == Xcvr.SFP:
         return True
      logging.debug('setting modsel for qsfp/osfp %s to %s', self.portNum, value)
      return self.rw.writeValue('modsel', '1' if value else '0')

   def getTxDisable(self):
      if self.xcvrType == Xcvr.SFP:
         return self.rw.readValue('txdisable')
      return False

   def setTxDisable(self, value):
      if self.xcvrType == Xcvr.SFP:
         logging.debug('setting txdisable for sfp %s to %s', self.portNum, value)
         return self.rw.writeValue('txdisable', '1' if value else '0')
      return False

   def getInterruptLine(self):
      return self.interruptLine

   def getReset(self):
      return self.reset

class ScdXcvrReset(Reset):
   def __init__(self, xcvr, typeStr):
      self.xcvr = xcvr
      self.name = '%s%d_reset' % (typeStr, self.xcvr.portNum)

   def read(self):
      return self.xcvr.rw.readValue('reset')

   def resetSim(self, value):
      logging.debug('resetting device %s', self.name)

   @simulateWith(resetSim)
   def reset(self, value):
      self.xcvr.rw.writeValue('reset', '1' if value else '0')

   def resetIn(self):
      self.reset(True)

   def resetOut(self):
      self.reset(False)
      self.xcvr.setModuleSelect(True)

   def getName(self):
      return self.name

class ScdKernelPsu(Psu):
   def __init__(self, psuId, rw, presenceGpios, statusGpios):
      self.psuId = psuId
      self.rw_ = rw
      self.presenceGpios_ = presenceGpios
      self.statusGpios_ = statusGpios

   def getPresence(self):
      return all(self.rw_.readValue(pin) == '1' for pin in self.presenceGpios_)

   def getStatus(self):
      if not self.statusGpios_:
         return self.getPresence()

      return all(self.rw_.readValue(pin) == '1' for pin in self.statusGpios_)

class ScdKernelDriver(PciKernelDriver):
   def __init__(self, scd):
      super(ScdKernelDriver, self).__init__(scd.addr, 'scd-hwmon')
      self.scd = scd

   def writeComponents(self, components, filename):
      PAGE_SIZE = 4096
      data = []
      data_size = 0

      for entry in components:
         entry_size = len(entry) + 1
         if entry_size + data_size > PAGE_SIZE:
            writeConfig(self.getSysfsPath(), {filename: '\n'.join(data)})
            data_size = 0
            data = []
         data.append(entry)
         data_size += entry_size

      if data:
         writeConfig(self.getSysfsPath(), {filename: '\n'.join(data)})

   def waitReadySim(self):
      logging.info('Waiting SCD %s.', os.path.join(self.getSysfsPath(),
                                                   'smbus_tweaks'))
      logging.info('Done.')

   @simulateWith(waitReadySim)
   def waitReady(self):
      path = os.path.join(self.getSysfsPath(), 'smbus_tweaks')
      logging.debug('Waiting SCD %s.', path)

      count = 0
      retries = 100
      while not os.path.exists(path) and count <= retries:
         time.sleep(SCD_WAIT_TIMEOUT / retries)
         count = count + 1
         logging.debug('Waiting SCD %s attempt %d.', path, count)
      if not os.path.exists(path):
         logging.error('Waiting SCD %s failed.', path)

   def refresh(self):
      # reload i2c bus cache
      masterName = "SCD %s SMBus master %d bus %d" % (self.addr, 0, 0)
      if not inSimulation():
         self.scd.i2cOffset = i2cBusFromName(masterName, force=True)
      else:
         self.scd.i2cOffset = 2

   def setup(self):
      super(ScdKernelDriver, self).setup()

      scd = self.scd
      data = []

      for addr, info in scd.masters.items():
         data += ["master %#x %d %d" % (addr, info['id'], info['bus'])]

      for addr, platform, num in scd.fanGroups:
         data += ["fan_group %#x %u %u" % (addr, platform, num)]

      for addr, name in scd.leds:
         data += ["led %#x %s" % (addr, name)]

      for addr, xcvrId in scd.osfps:
         data += ["osfp %#x %u" % (addr, xcvrId)]

      for addr, xcvrId in scd.qsfps:
         data += ["qsfp %#x %u" % (addr, xcvrId)]

      for addr, xcvrId in scd.sfps:
         data += ["sfp %#x %u" % (addr, xcvrId)]

      for reset in scd.resets:
         data += ["reset %#x %s %u" % (reset.addr, reset.name, reset.bit)]

      for gpio in scd.gpios:
         data += ["gpio %#x %s %u %d %d" % (gpio.addr, gpio.name, gpio.bit,
                                            int(gpio.ro), int(gpio.activeLow))]

      self.waitReady()

      logging.debug('creating scd objects')
      self.writeComponents(data, "new_object")

      for intrReg in scd.interrupts:
         intrReg.setup()

      self.refresh() # sync with kernel runtime state

      tweaks = []
      for tweak in scd.tweaks:
         tweaks += ["%#x %#x %#x %#x %#x %#x" % (
            tweak.addr.bus, tweak.addr.address, tweak.t, tweak.datr, tweak.datw,
            tweak.ed)]

      if tweaks:
         logging.debug('applying scd tweaks')
         self.writeComponents(tweaks, "smbus_tweaks")

   def finish(self):
      logging.debug('applying scd configuration')
      path = self.getSysfsPath()
      if Config().lock_scd_conf:
         writeConfig(path, {'init_trigger': '1'})
      super(ScdKernelDriver, self).finish()

   def resetSim(self, value):
      resets = self.scd.getSysfsResetNameList()
      logging.debug('resetting devices %s', resets)

   @simulateWith(resetSim)
   def reset(self, value):
      path = self.getSysfsPath()
      for reset in self.scd.getSysfsResetNameList():
         with open(os.path.join(path, reset), 'w') as f:
            f.write('1' if value else '0')

   def resetIn(self):
      self.reset(True)

   def resetOut(self):
      self.reset(False)

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
      if not inSimulation():
         self.clear()

   def set(self):
      self.reg.setMask(self.bit)

   def clear(self):
      self.reg.clearMask(self.bit)

   def getFile(self):
      return self.reg.scd.getUio(self.reg.num, self.bit)

class ScdInterruptRegister(object):
   def __init__(self, scd, addr, num):
      self.scd = scd
      self.num = num
      self.readAddr = addr
      self.setAddr = addr
      self.clearAddr = addr + 0x10
      self.statusAddr = addr + 0x20

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
         ('interrupt_mask%s' % self.num, str(0xffffffff)),
      ]))

   def getInterruptBit(self, bit):
      return ScdInterrupt(self, bit) if Config().init_irq else None

class Scd(PciComponent):
   BusTweak = namedtuple('BusTweak', 'addr, t, datr, datw, ed')
   def __init__(self, addr, **kwargs):
      super(Scd, self).__init__(addr)
      self.addDriver(KernelDriver, 'scd')
      self.addDriver(ScdKernelDriver, self)
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

   def createPowerCycle(self, reg=0x7000, wr=0xDEAD):
      powerCycle = ScdPowerCycle(self, reg=reg, wr=wr)
      self.powerCycles.append(powerCycle)
      return powerCycle

   def getPowerCycles(self):
      return self.powerCycles

   def createWatchdog(self, reg=0x0120):
      return ScdWatchdog(self, reg=reg)

   def createInterrupt(self, addr, num):
      interrupt = ScdInterruptRegister(self, addr, num)
      self.interrupts.append(interrupt)
      return interrupt

   def getMmap(self):
      if not self.mmapReady:
         # check that the scd driver is loaded the first time
         drv = self.drivers[0]
         if not drv.loaded():
            # This codepath is unlikely to be used
            drv.setup()
         self.mmapReady = True
      return MmapResource(os.path.join(self.pciSysfs, "resource0"))

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
      devAddr = self.i2cAddr(bus, Xcvr.ADDR)
      xcvr = ScdKernelXcvr(xcvrId, xcvrType, devAddr, self.pciSysfs,
                           interruptLine=interruptLine)
      # XXX: An abstraction should be added for the xcvr driver as it assumes kernel
      self.addComponent(I2cKernelComponent(devAddr, 'sff8436'))
      self.addBusTweak(devAddr)
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

   def createPsu(self, psuId, presenceGpios=['present'], statusGpios=['status', 'ac_status']):
      sysfs = ScdSysfsRW(psuId, 'psu', self.pciSysfs)
      presenceGpios = presenceGpios[:] if presenceGpios else []
      statusGpios = statusGpios[:] if statusGpios else []
      return ScdKernelPsu(psuId, sysfs, presenceGpios, statusGpios)

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
