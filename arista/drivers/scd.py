import copy
import os

from collections import OrderedDict

from .i2c import I2cDevDriver
from .pci import PciKernelDriver
from ..core import utils
from ..core.config import Config
from ..core.log import getLogger
from ..core.register import Register, ClearOnReadRegister
from ..core.utils import inSimulation

logging = getLogger(__name__)

SCD_WAIT_TIMEOUT = 5.

_i2cBuses = OrderedDict()
def getKernelI2cBuses(force=False):
   if _i2cBuses and not force:
      return _i2cBuses
   _i2cBuses.clear()
   buses = {}
   root = '/sys/class/i2c-adapter'
   for busName in sorted(os.listdir(root), key=lambda x: int(x[4:])):
      busId = int(busName.replace('i2c-', ''))
      with open(os.path.join(root, busName, 'name')) as f:
         buses[busId] = f.read().rstrip()
   return buses

def i2cBusFromName(name, idx=0, force=False):
   buses = getKernelI2cBuses(force=force)
   for busId, busName in buses.items():
      if name == busName:
         if idx > 0:
            idx -= 1
         else:
            return busId
   return None

class ScdKernelDriver(PciKernelDriver):
   def __init__(self, scd=None, **kwargs):
      self.scd = scd
      super(ScdKernelDriver, self).__init__(module='scd-hwmon', **kwargs)

   def __str__(self):
      return '%s(addr=%s)' % (self.__class__.__name__, self.addr)

   def writeComponents(self, components, filename):
      PAGE_SIZE = 4096
      data = []
      data_size = 0

      for entry in components:
         entry_size = len(entry) + 1
         if entry_size + data_size > PAGE_SIZE:
            utils.writeConfig(self.addr.getSysfsPath(), {filename: '\n'.join(data)})
            data_size = 0
            data = []
         data.append(entry)
         data_size += entry_size

      if data:
         utils.writeConfig(self.addr.getSysfsPath(), {filename: '\n'.join(data)})

   def waitReadySim(self):
      logging.info('Waiting SCD %s.', os.path.join(self.addr.getSysfsPath(),
                                                   'smbus_tweaks'))
      logging.info('Done.')

   @utils.simulateWith(waitReadySim)
   def waitReady(self):
      path = os.path.join(self.addr.getSysfsPath(), 'smbus_tweaks')
      utils.FileWaiter(path, SCD_WAIT_TIMEOUT).waitFileReady()

   def refresh(self):
      # reload i2c bus cache
      masterName = "SCD %s SMBus master %d bus %d" % (self.addr, 0, 0)
      if not utils.inSimulation():
         self.scd.i2cOffset = i2cBusFromName(masterName, force=True)
      else:
         self.scd.i2cOffset = 2

   def setup(self):
      super(ScdKernelDriver, self).setup()

      scd = self.scd
      data = []

      for addr, info in scd.smbusMasters.items():
         data += ["smbus_master %#x %d %d" % (addr, info['id'], info['bus'])]

      for addr, info in scd.mdioMasters.items():
         data += ["mdio_master %#x %d %d %d" % (addr, info['id'], info['bus'],
                                                info['speed'])]

      for mdio in scd.mdios:
         data += ["mdio_device %d %d %d %d %d %d" % \
                  (mdio.master, mdio.bus, mdio.id, mdio.portAddr, mdio.deviceAddr, \
                   mdio.clause)]

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

      if scd.msiRearmOffset:
         path = self.addr.getSysfsPath()
         utils.writeConfig(path, {'msi_rearm_offset': '%d' % scd.msiRearmOffset})
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
      path = self.addr.getSysfsPath()
      if Config().lock_scd_conf:
         utils.writeConfig(path, {'init_trigger': '1'})
      super(ScdKernelDriver, self).finish()

   def resetSim(self, value):
      resets = self.scd.getSysfsResetNameList()
      logging.debug('resetting devices %s', resets)

   @utils.simulateWith(resetSim)
   def reset(self, value):
      path = self.addr.getSysfsPath()
      for reset in self.scd.getSysfsResetNameList():
         with open(os.path.join(path, reset), 'w') as f:
            f.write('1' if value else '0')

   def resetIn(self):
      self.reset(True)

   def resetOut(self):
      self.reset(False)

class ScdResetRegister(Register):
   def __init__(self, addr, *fields, **kwargs):
      super(ScdResetRegister, self).__init__(addr, *fields, **kwargs)
      self.setAddr = addr
      self.clearAddr = addr + kwargs.get('clearOffset', 0x10)

   def writeBit(self, bitpos, value):
      if inSimulation():
         return

      if value:
         self.parent.write(self.setAddr, 1 << bitpos)
      else:
         self.parent.write(self.clearAddr, 1 << bitpos)

   def readBit(self, bitpos):
      if inSimulation():
         return 0

      return (self.parent.read(self.setAddr) >> bitpos) & 1

class ScdStatusChangedRegister(Register):
   def __init__(self, addr, *fields, **kwargs):
      super(ScdStatusChangedRegister, self).__init__(addr, *fields, **kwargs)

      fields = copy.deepcopy(fields)
      for field in fields:
         field.name = '%sChanged' % field.name
      self.changedRegister = ClearOnReadRegister(addr + 1, fields, **kwargs)

   def generateAttributes(self, parent=None):
      attrs = super(ScdStatusChangedRegister, self).generateAttributes(parent)
      attrs.update(self.changedRegister.generateAttributes(parent))
      return attrs

class ScdI2cDevDriver(I2cDevDriver):
   pass
