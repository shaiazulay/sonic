from ..inventory.led import Led

class LedImpl(Led):
   def __init__(self, name=None, driver=None, **kwargs):
      self.name = name
      self.driver = driver
      self.__dict__.update(kwargs)

   def getColor(self):
      return self.driver.getLedColor(self)

   def setColor(self, color):
      return self.driver.setLedColor(self, color)

   def getName(self):
      return self.name

   def isStatusLed(self):
      return not 'sfp' in self.name
