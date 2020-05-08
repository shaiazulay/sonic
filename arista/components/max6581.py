from ..core.component import Priority

from ..drivers.max6581 import Max6581KernelDriver
from ..drivers.sysfs import TempSysfsDriver

from .common import I2cComponent
from .mixin import TempComponentMixin

class Max6581(I2cComponent, TempComponentMixin):
   def __init__(self, addr=None, drivers=None, priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [Max6581KernelDriver(addr=addr),
                            TempSysfsDriver(driverName='tempDriver', addr=addr)]
      super(Max6581, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                    **kwargs)
