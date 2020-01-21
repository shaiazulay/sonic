import os

from .sysfs import FanSysfsDriver

from ..core.driver import Driver, KernelDriver
from ..core import utils
from ..core.log import getLogger

logging = getLogger(__name__)

class I2cKernelDriver(Driver):
   def __init__(self, name=None, addr=None, waitFile=None, waitTimeout=None,
                module=None, **kwargs):
      self.name = name
      self.addr = addr
      if module:
         self.kernelDriver = KernelDriver(module=module, **kwargs)
      else:
         self.kernelDriver = None
      self.fileWaiter = utils.FileWaiter(waitFile, waitTimeout)
      super(I2cKernelDriver, self).__init__(**kwargs)

   def getSysfsPath(self):
      return self.addr.getSysfsPath()

   def getSysfsBusPath(self):
      return '/sys/bus/i2c/devices/i2c-%d' % self.addr.bus

   def setup(self):
      if self.kernelDriver:
         self.kernelDriver.setup()
      addr = self.addr
      devicePath = self.getSysfsPath()
      path = os.path.join(self.getSysfsBusPath(), 'new_device')
      logging.debug('creating i2c device %s on bus %d at 0x%02x',
                    self.name, addr.bus, addr.address)
      if utils.inSimulation():
         return
      if os.path.exists(devicePath):
         logging.debug('i2c device %s already exists', devicePath)
      else:
         with open(path, 'w') as f:
            f.write('%s 0x%02x' % (self.name, self.addr.address))
         self.fileWaiter.waitFileReady()
      super(I2cKernelDriver, self).setup()

   def clean(self):
      # i2c kernel devices are automatically cleaned when the module is removed
      if utils.inSimulation():
         return
      path = os.path.join(self.getSysfsBusPath(), 'delete_device')
      addr = self.addr
      if os.path.exists(self.getSysfsPath()):
         logging.debug('removing i2c device %s from bus %d', self.name, addr.bus)
         with open(path, 'w') as f:
            f.write('0x%02x' % addr.address)
      if self.kernelDriver:
         self.kernelDriver.clean()
      super(I2cKernelDriver, self).clean()

   def __str__(self):
      return '%s(name=%s)' % (self.__class__.__name__, self.name)

class I2cKernelFanDriver(I2cKernelDriver):
   def __init__(self, maxPwm=255, addr=None, waitFile=None, **kwargs):
      self.sysfsDriver = FanSysfsDriver(maxPwm=maxPwm, addr=addr, **kwargs)
      super(I2cKernelFanDriver, self).__init__(addr=addr, waitFile=waitFile,
                                               **kwargs)

   def setup(self):
      super(I2cKernelFanDriver, self).setup()
      self.sysfsDriver.setup()

   def clean(self):
      self.sysfsDriver.clean()
      super(I2cKernelFanDriver, self).clean()

   def getFanSpeed(self, fan):
      return self.sysfsDriver.getFanSpeed(fan)

   def setFanSpeed(self, fan, speed):
      return self.sysfsDriver.setFanSpeed(fan, speed)

   def getFanPresence(self, fan):
      return self.sysfsDriver.getFanPresence(fan)

   def getFanStatus(self, fan):
      return self.sysfsDriver.getFanStatus(fan)

   def getFanDirection(self, fan):
      return self.sysfsDriver.getFanDirection(fan)
