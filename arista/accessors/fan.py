from ..core.inventory import Fan

class FanImpl(Fan):
   def __init__(self, driver=None, led=None, **kwargs):
      self.driver = driver
      self.led = led
      self.__dict__.update(kwargs)

   def getSpeed(self):
      return self.driver.getFanSpeed(self)

   def setSpeed(self, speed):
      return self.driver.setFanSpeed(self, speed)

   def getDirection(self):
      return self.driver.getFanDirection(self)

   def getLed(self):
      return self.led
