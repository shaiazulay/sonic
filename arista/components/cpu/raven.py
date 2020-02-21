from ..common import I2cComponent

from ...accessors.fan import FanImpl
from ...accessors.led import LedImpl

from ...core.driver import KernelDriver
from ...core.log import getLogger

from ...drivers.sysfs import FanSysfsDriver, LedSysfsDriver

logging = getLogger(__name__)

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

