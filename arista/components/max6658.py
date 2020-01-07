
from .common import I2cComponent
from ..core.component import Priority
from ..drivers.max6658 import Max6658KernelDriver

class Max6658(I2cComponent):
   def __init__(self, addr, drivers=None,
                priority=Priority.THERMAL, **kwargs):
      drivers = drivers or [ Max6658KernelDriver(addr=addr) ]
      self.sensors = []
      super(Max6658, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                    **kwargs)

   def addTempSensors(self, sensors):
      self.sensors.extend(sensors)
