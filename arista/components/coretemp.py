from ..core.component import PciComponent, Priority

from ..drivers.sysfs import TempSysfsDriver

from .mixin import TempComponentMixin

class Coretemp(PciComponent, TempComponentMixin):
   def __init__(self, drivers=None, priority=Priority.THERMAL,
                waitFile='/sys/class/hwmon/hwmon1', **kwargs):
      drivers = drivers or [TempSysfsDriver(driverName='tempDriver',
         sysfsPath='/sys/devices/platform/coretemp.0/hwmon/hwmon1')]
      super(Coretemp, self).__init__(drivers=drivers, priority=priority,
                                     waitFile=waitFile, **kwargs)
