import logging

from ..core.driver import KernelDriver
from .common import I2cComponent

from ..drivers.accessors import FanImpl
from ..drivers.i2c import I2cFanDriver
from ..drivers.sysfs import SysfsDriver

class CrowFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, **kwargs):
      drivers = drivers or [KernelDriver(module='crow-fan-driver'),
                            I2cFanDriver(name='crow_cpld', addr=addr, maxPwm=255)]
      super(CrowFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                                 **kwargs)

   def createFan(self, fanId, driver='I2cFanDriver', **kwargs):
      logging.debug('creating crow fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)

class LAFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, **kwargs):
      drivers = drivers or [KernelDriver(module='rook-fan-cpld'),
                            I2cFanDriver(name='la_cpld', addr=addr, maxPwm=255)]
      super(LAFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                               **kwargs)

   def createFan(self, fanId, driver='I2cFanDriver', **kwargs):
      logging.debug('creating LA fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)

class TehamaFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, **kwargs):
      drivers = drivers or [KernelDriver(module='rook-fan-cpld'),
                            I2cFanDriver(name='tehama_cpld', addr=addr, maxPwm=255)]
      super(TehamaFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                                   **kwargs)

   def createFan(self, fanId, driver='I2cFanDriver', **kwargs):
      logging.debug('creating Tehama fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)

class RavenFanCpldComponent(I2cComponent):
   def __init__(self, drivers=None, **kwargs):
      sysfsDriver = SysfsDriver(maxPwm=255,
            sysfsPath='/sys/devices/platform/sb800-fans/hwmon/hwmon1')
      drivers = drivers or [KernelDriver(module='raven-fan-driver'), sysfsDriver]
      super(RavenFanCpldComponent, self).__init__(drivers=drivers, **kwargs)

   def createFan(self, fanId, driver='SysfsDriver', **kwargs):
      logging.debug('creating raven fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)
