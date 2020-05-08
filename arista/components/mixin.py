from ..accessors.temp import TempImpl

from ..core.component import Component

class TempComponentMixin(Component):
   def __init__(self, sensors=None, **kwargs):
      super(TempComponentMixin, self).__init__(sensors=sensors, **kwargs)
      sensors = sensors or []
      self.addTempSensors(sensors)

   def addTempSensors(self, sensors):
      for sensor in sensors:
         self.inventory.addTemp(TempImpl(sensor, self.drivers['tempDriver']))
