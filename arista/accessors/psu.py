from ..core.inventory import Psu

class PsuImpl(Psu):
   def __init__(self, driver=None, led=None, **kwargs):
      self.driver = driver
      self.statusGpio = True
      self.led = led
      self.__dict__.update(kwargs)

   def getPresence(self):
      return self.driver.getPsuPresence(self)

   def getStatus(self):
      return self.driver.getPsuStatus(self)

   def getLed(self):
      return self.led

class MixedPsuImpl(Psu):
   def __init__(self, presenceDriver=None, statusDriver=None, led=None, **kwargs):
      self.presenceDriver = presenceDriver
      self.statusDriver = statusDriver
      self.led = led
      self.__dict__.update(kwargs)

   def getPresence(self):
      return self.presenceDriver.getPsuPresence(self)

   def getStatus(self):
      return self.statusDriver.getPsuStatus(self)

   def getLed(self):
      return self.led
