from ..core.component import Priority

from ..drivers.max6658 import Max6658KernelDriver
from ..drivers.sysfs import TempSysfsDriver

from .common import I2cComponent
from .mixin import TempComponentMixin

class Max6658(I2cComponent, TempComponentMixin):
   def __init__(self, addr=None, drivers=None, priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [Max6658KernelDriver(addr=addr),
                            TempSysfsDriver(driverName='tempDriver', addr=addr)]
      super(Max6658, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                    **kwargs)
