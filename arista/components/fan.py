from ..accessors.fan import FanImpl
from ..accessors.led import LedImpl

from ..core.driver import KernelDriver
from ..core.log import getLogger

from ..drivers.i2c import I2cKernelFanDriver
from ..drivers.sysfs import FanSysfsDriver, LedSysfsDriver

from .common import I2cComponent, PciComponent

logging = getLogger(__name__)

class LAFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, waitFile=None, **kwargs):
      if not drivers:
         fanSysfsDriver = I2cKernelFanDriver(name='la_cpld',
               module='rook-fan-cpld', addr=addr, maxPwm=255, waitFile=waitFile)
         ledSysfsDriver = LedSysfsDriver(sysfsPath='/sys/class/leds')
         drivers = [fanSysfsDriver, ledSysfsDriver]
      super(LAFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                               **kwargs)

   def createFan(self, fanId, driver='I2cKernelFanDriver',
                 ledDriver='LedSysfsDriver', **kwargs):
      logging.debug('creating LA fan %s', fanId)
      driver = self.drivers[driver]
      led = LedImpl(name='fan%s' % fanId, driver=self.drivers[ledDriver])
      return FanImpl(fanId=fanId, driver=driver, led=led, **kwargs)

class TehamaFanCpldComponent(I2cComponent):
   def __init__(self, addr=None, drivers=None, waitFile=None, **kwargs):
      if not drivers:
         fanSysfsDriver = I2cKernelFanDriver(name='tehama_cpld',
               module='rook-fan-cpld', addr=addr, maxPwm=255, waitFile=waitFile)
         ledSysfsDriver = LedSysfsDriver(sysfsPath='/sys/class/leds')
         drivers = [fanSysfsDriver, ledSysfsDriver]
      super(TehamaFanCpldComponent, self).__init__(addr=addr, drivers=drivers,
                                                   **kwargs)

   def createFan(self, fanId, driver='I2cKernelFanDriver',
                 ledDriver='LedSysfsDriver', **kwargs):
      logging.debug('creating Tehama fan %s', fanId)
      driver = self.drivers[driver]
      led = LedImpl(name='fan%s' % fanId, driver=self.drivers[ledDriver])
      return FanImpl(fanId=fanId, driver=driver, led=led, **kwargs)

class RavenFanCpldComponent(I2cComponent):
   def __init__(self, drivers=None, waitFile=None, **kwargs):
      if not drivers:
         fanSysfsDriver = FanSysfsDriver(maxPwm=255,
               sysfsPath='/sys/devices/platform/sb800-fans/hwmon/hwmon1',
               waitFile=waitFile)
         ledSysfsDriver = LedSysfsDriver(sysfsPath='/sys/class/leds')
         drivers = [KernelDriver(module='raven-fan-driver'), fanSysfsDriver,
                    ledSysfsDriver]
      super(RavenFanCpldComponent, self).__init__(drivers=drivers, **kwargs)

   def createFan(self, fanId, driver='FanSysfsDriver', ledDriver='LedSysfsDriver',
                 **kwargs):
      logging.debug('creating raven fan %s', fanId)
      driver = self.drivers[driver]
      led = LedImpl(name='fan%s' % fanId, driver=self.drivers[ledDriver])
      return FanImpl(fanId=fanId, driver=driver, led=led, **kwargs)

class ScdFanComponent(PciComponent):
   def __init__(self, drivers=None, waitFile=None, **kwargs):
      fanSysfsDriver = FanSysfsDriver(maxPwm=255,
            sysfsPath='/sys/devices/pci0000:00/0000:00:09.0/hwmon/hwmon2',
            waitFile=waitFile)
      ledSysfsDriver = LedSysfsDriver(sysfsPath='/sys/class/leds')
      drivers = drivers or [fanSysfsDriver, ledSysfsDriver]
      super(ScdFanComponent, self).__init__(drivers=drivers, **kwargs)

   def createFan(self, fanId, driver='FanSysfsDriver', ledDriver='LedSysfsDriver',
                 ledId=None, **kwargs):
      logging.debug('creating scd fan %s', fanId)
      driver = self.drivers[driver]
      ledId = ledId or fanId
      led = LedImpl(name='fan%s' % ledId, driver=self.drivers[ledDriver])
      return FanImpl(fanId=fanId, driver=driver, led=led, **kwargs)
