
from ..inventory.temp import Temp

class TempImpl(Temp):
   def __init__(self, sensor, driver=None, **kwargs):
      self.sensor = sensor
      self.name = sensor.name
      self.driver = driver

   def getTemperature(self):
      return self.driver.getTemperature(self.sensor)

   def getLowThreshold(self):
      return self.driver.getLowThreshold(self.sensor)

   def setLowThreshold(self, value):
      return self.driver.setLowThreshold(self.sensor, value)

   def getHighThreshold(self):
      return self.driver.getHighThreshold(self.sensor)

   def setHighThreshold(self, value):
      return self.driver.setHighThreshold(self.sensor, value)

