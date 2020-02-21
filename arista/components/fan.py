from ..accessors.fan import FanImpl
from ..accessors.led import LedImpl

from ..core.log import getLogger

from ..drivers.sysfs import FanSysfsDriver, LedSysfsDriver

from .common import PciComponent

logging = getLogger(__name__)

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
