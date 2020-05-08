
from .common import I2cComponent
from ..accessors.temp import TempImpl
from ..core.component import Priority
from ..drivers.lm75 import Lm75KernelDriver
from ..drivers.sysfs import TempSysfsDriver

class Lm75(I2cComponent):
   def __init__(self, addr, drivers=None,
                priority=Priority.THERMAL, sensors=None, **kwargs):
      drivers = drivers or [Lm75KernelDriver(addr=addr),
                            TempSysfsDriver(addr=addr)]
      self.sensors = []
      super(Lm75, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                 **kwargs)
      if sensors:
         self.addTempSensors(sensors)

   def addTempSensors(self, sensors):
      self.sensors.extend(sensors)
      for sensor in sensors:
         self.inventory.addTemp(TempImpl(sensor, self.drivers['TempSysfsDriver']))

Tmp75 = Lm75
