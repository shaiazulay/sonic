
from .common import I2cComponent
from ..core.component import Priority
from ..drivers.tmp468 import Tmp468KernelDriver

class Tmp468(I2cComponent):
   def __init__(self, addr, drivers=None,
                priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [ Tmp468KernelDriver(addr=addr) ]
      self.sensors = []
      super(Tmp468, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                   **kwargs)

   def addTempSensors(self, sensors):
      self.sensors.extend(sensors)
