from __future__ import print_function, with_statement

import logging
import os
import time

from collections import OrderedDict, namedtuple

from ..core.inventory import Xcvr, PowerCycle, Psu, Watchdog
from ..core.utils import getMmap, simulateWith, writeConfig

from .common import PciComponent, KernelDriver, PciKernelDriver

SCD_WAIT_TIMEOUT = 5.

class ScdSysfsGroup(object):
   def __init__(self, objNum, typeStr, driver):
      self.driver = driver
      self.prefix = '%s%d_' % (typeStr, objNum)
      self.prefixPath = os.path.join(driver.getSysfsPath(), self.prefix)

class ScdSysfsRW(ScdSysfsGroup):
   def __init__(self, objNum, typeStr, driver):
      ScdSysfsGroup.__init__(self, objNum, typeStr, driver)

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
   def __init__(self, portNum, xcvrType, eepromAddr, bus, driver, sysfsRWClass):
      Xcvr.__init__(self, portNum, xcvrType, eepromAddr, bus)
      typeStr = 'qsfp' if xcvrType == Xcvr.QSFP else 'sfp'
      self.rw = sysfsRWClass(portNum, typeStr, driver)

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
      logging.debug('setting modsel for qsfp %s to %s', self.portNum, value)
      return self.rw.writeValue('modsel', '1' if value else '0')

   def reset(self, value):
      if self.xcvrType == Xcvr.SFP:
         return False
      return self.rw.writeValue('reset', '1' if value else '0')

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
      super(ScdKernelDriver, self).__init__(scd, 'scd-hwmon')

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

   def setup(self):
      super(ScdKernelDriver, self).setup()

      scd = self.component
      data = []

      for addr, info in scd.masters.items():
         data += ["master %#x %d %d" % (addr, info['id'], info['bus'])]

      for addr, name in scd.leds:
         data += ["led %#x %s" % (addr, name)]

      for addr, xcvrId in scd.qsfps:
         data += ["qsfp %#x %u" % (addr, xcvrId)]

      for addr, xcvrId in scd.sfps:
         data += ["sfp %#x %u" % (addr, xcvrId)]

      for reset in scd.resets:
         data += ["reset %#x %s %u" % (reset.addr, reset.name, reset.bit)]

      for gpio in scd.gpios:
         data += ["gpio %#x %s %u %d %d" % (gpio.addr, gpio.name, gpio.bit,
                                            int(gpio.ro), int(gpio.activeLow))]

      tweaks = []
      for tweak in scd.tweaks:
         tweaks += ["%#x %#x %#x %#x %#x %#x" % (
            tweak.bus, tweak.addr, tweak.t, tweak.datr, tweak.datw, tweak.ed)]

      self.waitReady()

      logging.debug('creating scd objects')
      self.writeComponents(data, "new_object")

      if tweaks:
         logging.debug('applying scd tweaks')
         self.writeComponents(tweaks, "smbus_tweaks")

   def finish(self):
      logging.debug('applying scd configuration')
      path = self.getSysfsPath()
      writeConfig(path, {'init_trigger': '1'})
      super(ScdKernelDriver, self).finish()

   def resetSim(self, value):
      resets = self.component.getSysfsResetNameList()
      logging.debug('reseting devices %s', resets)

   @simulateWith(resetSim)
   def reset(self, value):
      path = self.getSysfsPath()
      for reset in self.component.getSysfsResetNameList():
         with open(os.path.join(path, reset), 'w') as f:
            f.write('1' if value else '0')

   def resetIn(self):
      self.reset(True)

   def resetOut(self):
      self.reset(False)

class ScdWatchdog(Watchdog):
   def __init__(self, driver, path, reg=0x0120):
      self.driver = driver
      self.path = path
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
         with getMmap(self.driver, self.path) as mmap:
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
         with getMmap(self.driver, self.path) as mmap:
            regValue = mmap.read32(self.reg)
            enabled = bool(regValue >> 31)
            timeout = regValue & ((1<<16)-1)
         return { "enabled": enabled, "timeout": timeout }
      except RuntimeError as e:
         logging.error("watchdog status error: {}".format(e))
         return None

class ScdPowerCycle(PowerCycle):
   def __init__(self, driver=None, path=None, reg=0x7000, wr=0xDEAD):
      self.driver = driver
      self.path = path
      self.reg = reg
      self.wr = wr

   def powerCycle(self):
      logging.info("Initiating powercycle through SCD")
      try:
         with getMmap(self.driver, self.path) as mmap:
            mmap.write32(self.reg, self.wr)
            logging.info("Powercycle triggered by SCD")
            return True
      except RuntimeError as e:
         logging.error("powercycle error: %s", e)
         return False

class Scd(PciComponent):
   BusTweak = namedtuple('BusTweak', 'bus, addr, t, datr, datw, ed')
   def __init__(self, addr, **kwargs):
      super(Scd, self).__init__(addr)
      self.addDriver(KernelDriver, 'scd')
      self.addDriver(ScdKernelDriver)
      self.rwCls = ScdSysfsRW
      self.masters = OrderedDict()
      self.resets = []
      self.gpios = []
      self.powerCycles = []
      self.qsfps = []
      self.sfps = []
      self.leds = []
      self.tweaks = []
      self.xcvrs = []

   def createPowerCycle(self, reg=0x7000, wr=0xDEAD):
      powerCycle = ScdPowerCycle(driver=KernelDriver(self, "scd"),
                                 path=os.path.join(self.getSysfsPath(), "resource0"),
                                 reg=reg, wr=wr)
      self.powerCycles.append(powerCycle)
      return powerCycle

   def getPowerCycles(self):
      return self.powerCycles

   def createWatchdog(self, reg=0x0120):
      return ScdWatchdog(KernelDriver(self, "scd"),
                         os.path.join(self.getSysfsPath(), "resource0"),
                         reg=reg)

   def addBusTweak(self, bus, addr, t=1, datr=1, datw=3, ed=0):
      self.tweaks.append(Scd.BusTweak(bus, addr, t, datr, datw, ed))

   def addSmbusMaster(self, addr, mid, bus=8):
      self.masters[addr] = {
         'id': mid,
         'bus': bus,
      }

   def addSmbusMasterRange(self, addr, count, spacing=0x100, bus=8):
      addrs = range(addr, addr + (count + 1) * spacing, spacing)
      for i, addr in enumerate(addrs, 0):
         self.addSmbusMaster(addr, i, bus)

   def addLed(self, addr, name):
      self.leds += [(addr, name)]

   def addLeds(self, leds):
      self.leds += leds

   def addReset(self, gpio):
      self.resets += [gpio]

   def addResets(self, gpios):
      self.resets += gpios

   def addGpio(self, gpio):
      self.gpios += [gpio]

   def addGpios(self, gpios):
      self.gpios += gpios

   def addQsfp(self, addr, xcvrId, bus, eepromAddr=0x50):
      self.qsfps += [(addr, xcvrId)]
      xcvr = ScdKernelXcvr(xcvrId, Xcvr.QSFP, eepromAddr, bus, self.drivers[1],
                           self.rwCls)
      self.xcvrs.append(xcvr)
      return xcvr

   def addSfp(self, addr, xcvrId, bus, eepromAddr=0x50):
      self.sfps += [(addr, xcvrId)]
      xcvr = ScdKernelXcvr(xcvrId, Xcvr.SFP, eepromAddr, bus, self.drivers[1],
                           self.rwCls)
      self.xcvrs.append(xcvr)
      return xcvr

   def createPsu(self, psuId, presenceGpios=['present'], statusGpios=['status', 'ac_status']):
      sysfs = self.rwCls(psuId, 'psu', self.drivers[1])
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

      gpios = []
      gpios += zipXcvr("sfp", sfp_names, self.sfps)
      gpios += zipXcvr("qsfp", qsfp_names, self.qsfps)
      gpios += [ (gpio.name, gpio.ro) for gpio in self.gpios ]
      gpios += [ (reset.name, False) for reset in self.resets ]

      return gpios

   def getSysfsResetNameList(self, xcvrs=True):
      entries = [reset.name for reset in self.resets]
      if xcvrs:
         entries += ['qsfp%d_reset' % xcvrId for _, xcvrId in self.qsfps]
      return entries

   def resetOut(self):
      super(Scd, self).resetOut()
      for xcvr in self.xcvrs:
         xcvr.setModuleSelect(True)

