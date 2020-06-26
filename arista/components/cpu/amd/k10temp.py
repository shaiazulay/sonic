from ....core.component import PciComponent, Priority
from ....core.types import PciAddr

from ....drivers.sysfs import TempSysfsDriver

from ...mixin import TempComponentMixin

class K10Temp(PciComponent, TempComponentMixin):
   def __init__(self, addr=PciAddr(bus=0x00, device=0x18, func=3), drivers=None,
                priority=Priority.THERMAL, waitFile='/sys/class/hwmon/hwmon0',
                **kwargs):
      drivers = drivers or [TempSysfsDriver(driverName='tempDriver', addr=addr)]
      super(K10Temp, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                    waitFile=waitFile, **kwargs)
