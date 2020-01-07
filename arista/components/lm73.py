
from .common import I2cComponent
from ..core.component import Priority
from ..drivers.lm73 import Lm73KernelDriver

class Lm73(I2cComponent):
   def __init__(self, addr, drivers=None,
                priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [ Lm73KernelDriver(addr=addr) ]
      self.sensors = []
      super(Lm73, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                 **kwargs)

   def addTempSensors(self, sensors):
      self.sensors.extend(sensors)
