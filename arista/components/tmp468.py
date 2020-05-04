
from .common import I2cComponent
from ..accessors.temp import TempImpl
from ..core.component import Priority
from ..drivers.sysfs import TempSysfsDriver
from ..drivers.tmp468 import Tmp468KernelDriver

class Tmp468(I2cComponent):
   def __init__(self, addr, drivers=None,
                priority=Priority.THERMAL, sensors=None, kname='tmp468',
                remoteCount=8, **kwargs):
      drivers = drivers or [Tmp468KernelDriver(addr=addr, name=kname),
                            TempSysfsDriver(addr=addr)]
      self.sensors = []
      super(Tmp468, self).__init__(addr=addr, drivers=drivers, priority=priority,
                                   **kwargs)
      if sensors:
         self.addTempSensors(sensors)

   def addTempSensors(self, sensors):
      self.sensors.extend(sensors)
      for sensor in sensors:
         self.inventory.addTemp(TempImpl(sensor, self.drivers['TempSysfsDriver']))
