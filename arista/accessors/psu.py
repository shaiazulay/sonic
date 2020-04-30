from ..inventory.psu import Psu

class PsuImpl(Psu):
   def __init__(self, psuId=1, driver=None, led=None, **kwargs):
      self.psuId = psuId
      self.driver = driver
      self.led = led
      self.__dict__.update(kwargs)

   def getName(self):
      return 'psu%s' % self.psuId

   def getPresence(self):
      return self.driver.getPsuPresence(self)

   def getStatus(self):
      return self.driver.getPsuStatus(self)

   def getLed(self):
      return self.led

class MixedPsuImpl(Psu):
   def __init__(self, psuId=1, presenceDriver=None, statusDriver=None, led=None,
                **kwargs):
      self.psuId = psuId
      self.presenceDriver = presenceDriver
      self.statusDriver = statusDriver
      self.led = led
      self.__dict__.update(kwargs)

   def getName(self):
      return 'psu%s' % self.psuId

   def getPresence(self):
      return self.presenceDriver.getPsuPresence(self)

   def getStatus(self):
      return self.statusDriver.getPsuStatus(self)

   def getLed(self):
      return self.led
