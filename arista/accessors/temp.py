
from ..inventory.temp import Temp
from ..core.log import getLogger

logging = getLogger(__name__)

class TempImpl(Temp):
   def __init__(self, sensor, driver=None, **kwargs):
      self.sensor = sensor
      self.name = sensor.name
      self.driver = driver
      self.__dict__.update(kwargs)

   def getName(self):
      return self.name

   def getPresence(self):
      return self.driver.getPresence(self.sensor)

   def getTemperature(self):
      return self.driver.getTemperature(self.sensor)

   def getLowThreshold(self):
      return self.driver.getLowThreshold(self.sensor)

   def setLowThreshold(self, value):
      return self.driver.setLowThreshold(self.sensor, value)

   def getHighThreshold(self):
      try:
         return float(self.sensor.critical)
      except AttributeError:
         logging.debug("%s sensor missing 'critical' attribute" % self.name)
         return self.driver.getHighThreshold(self.sensor)

   def setHighThreshold(self, value):
      try:
         self.sensor.critical = value
      except AttributeError:
         logging.debug("%s sensor missing 'critical' attribute" % self.name)
      return self.driver.setHighThreshold(self.sensor, value)
