from ....core.component import PciComponent, Priority

from ....drivers.sysfs import TempSysfsDriver

from ...mixin import TempComponentMixin

class Pch(PciComponent, TempComponentMixin):
   def __init__(self, drivers=None, priority=Priority.THERMAL,
                waitFile='/sys/class/hwmon/hwmon0', **kwargs):
      drivers = drivers or [TempSysfsDriver(driverName='tempDriver',
                            sysfsPath='/sys/devices/virtual/thermal/thermal_zone0/hwmon0')]
      super(Pch, self).__init__(drivers=drivers, priority=priority,
                                waitFile=waitFile, **kwargs)
