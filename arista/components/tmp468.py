from ..core.component import Priority

from ..drivers.sysfs import TempSysfsDriver
from ..drivers.tmp468 import Tmp468KernelDriver

from .common import I2cComponent
from .mixin import TempComponentMixin

class Tmp468(I2cComponent, TempComponentMixin):
   def __init__(self, addr=None, drivers=None, priority=Priority.THERMAL,
                kname='tmp468', remoteCount=8, **kwargs):
      drivers = drivers or [Tmp468KernelDriver(addr=addr, name=kname),
                            TempSysfsDriver(driverName='tempDriver', addr=addr)]
      super(Tmp468, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                   kname=kname, remoteCount=remoteCount, **kwargs)
