import logging
import os

from .sysfs import FanSysfsDriver

from ..core.driver import Driver
from ..core.utils import FileWaiter, inSimulation, locateHwmonPath

class I2cKernelDriver(Driver):
   def __init__(self, name=None, addr=None, waitFile=None, waitTimeout=None,
                **kwargs):
      self.name = name
      self.addr = addr
      self.fileWaiter = FileWaiter(waitFile, waitTimeout)
      super(I2cKernelDriver, self).__init__(**kwargs)

   def getSysfsPath(self):
      return self.addr.getSysfsPath()

   def getSysfsBusPath(self):
      return '/sys/bus/i2c/devices/i2c-%d' % self.addr.bus

   def setup(self):
      addr = self.addr
      devicePath = self.getSysfsPath()
      path = os.path.join(self.getSysfsBusPath(), 'new_device')
      logging.debug('creating i2c device %s on bus %d at 0x%02x',
                    self.name, addr.bus, addr.address)
      if inSimulation():
         return
      if os.path.exists(devicePath):
         logging.debug('i2c device %s already exists', devicePath)
      else:
         with open(path, 'w') as f:
            f.write('%s 0x%02x' % (self.name, self.addr.address))
         self.fileWaiter.waitFileReady()

   def clean(self):
      # i2c kernel devices are automatically cleaned when the module is removed
      if inSimulation():
         return
      path = os.path.join(self.getSysfsBusPath(), 'delete_device')
      addr = self.addr
      if os.path.exists(self.getSysfsPath()):
         logging.debug('removing i2c device %s from bus %d', self.name, addr.bus)
         with open(path, 'w') as f:
            f.write('0x%02x' % addr.address)

   def __str__(self):
      return '%s(name=%s)' % (self.__class__.__name__, self.name)

class I2cFanDriver(I2cKernelDriver, FanSysfsDriver):
   def __init__(self, maxPwm=255, addr=None, waitTimeout=1.0, **kwargs):
      self.waitTimeout = waitTimeout
      super(I2cFanDriver, self).__init__(maxPwm=maxPwm, addr=addr, **kwargs)

   def setup(self):
      super(I2cFanDriver, self).setup()
      locateHwmonPath(self.sysfsPath, self.addr.getSysfsPath(), self.waitTimeout,
                      'pwm')
