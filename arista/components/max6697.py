from ..core.component import Priority

from ..drivers.max6697 import Max6697KernelDriver
from ..drivers.sysfs import TempSysfsDriver

from .common import I2cComponent
from .mixin import TempComponentMixin

class Max6697(I2cComponent, TempComponentMixin):
   def __init__(self, addr=None, drivers=None, priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [Max6697KernelDriver(addr=addr),
                            TempSysfsDriver(driverName='tempDriver', addr=addr)]
      super(Max6697, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                    **kwargs)
