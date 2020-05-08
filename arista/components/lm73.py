from ..core.component import Priority

from ..drivers.lm73 import Lm73KernelDriver
from ..drivers.sysfs import TempSysfsDriver

from .common import I2cComponent
from .mixin import TempComponentMixin

class Lm73(I2cComponent, TempComponentMixin):
   def __init__(self, addr=None, drivers=None, priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [Lm73KernelDriver(addr=addr),
                            TempSysfsDriver(driverName='tempDriver', addr=addr)]
      super(Lm73, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                 **kwargs)
