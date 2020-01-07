
from .common import I2cComponent
from ..core.component import Priority
from ..drivers.max6581 import Max6581KernelDriver

class Max6581(I2cComponent):
   def __init__(self, addr, drivers=None,
                priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [ Max6581KernelDriver(addr=addr) ]
      self.sensors = []
      super(Max6581, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                    **kwargs)

   def addTempSensors(self, sensors):
      self.sensors.extend(sensors)
