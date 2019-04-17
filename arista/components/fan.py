import logging

from ..core.driver import KernelDriver
from .common import I2cComponent

from ..drivers.accessors import FanImpl
from ..drivers.i2c import I2cKernelFanDriver
from ..drivers.sysfs import FanSysfsDriver

class CrowFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, waitFile=None, **kwargs):
      drivers = drivers or [I2cKernelFanDriver(name='crow_cpld',
         module='crow-fan-driver', addr=addr, maxPwm=255, waitFile=waitFile)]
      super(CrowFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                                 **kwargs)

   def createFan(self, fanId, driver='I2cKernelFanDriver', **kwargs):
      logging.debug('creating crow fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)

class LAFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, waitFile=None, **kwargs):
      drivers = drivers or [I2cKernelFanDriver(name='la_cpld',
         module='rook-fan-cpld', addr=addr, maxPwm=255, waitFile=waitFile)]
      super(LAFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                               **kwargs)

   def createFan(self, fanId, driver='I2cKernelFanDriver', **kwargs):
      logging.debug('creating LA fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)

class TehamaFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, waitFile=None, **kwargs):
      drivers = drivers or [I2cKernelFanDriver(name='tehama_cpld',
         module='rook-fan-cpld', addr=addr, maxPwm=255, waitFile=waitFile)]
      super(TehamaFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                                   **kwargs)

   def createFan(self, fanId, driver='I2cKernelFanDriver', **kwargs):
      logging.debug('creating Tehama fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)

class RavenFanCpldComponent(I2cComponent):
   def __init__(self, drivers=None, waitFile=None, **kwargs):
      sysfsDriver = FanSysfsDriver(maxPwm=255,
            sysfsPath='/sys/devices/platform/sb800-fans/hwmon/hwmon1',
            waitFile=waitFile)
      drivers = drivers or [KernelDriver(module='raven-fan-driver'), sysfsDriver]
      super(RavenFanCpldComponent, self).__init__(drivers=drivers, **kwargs)

   def createFan(self, fanId, driver='FanSysfsDriver', **kwargs):
      logging.debug('creating raven fan %s', fanId)
      return FanImpl(fanId=fanId, driver=self.drivers[driver], **kwargs)
