from ..core.inventory import Fan

class FanImpl(Fan):
   def __init__(self, fanId=1, driver=None, led=None, **kwargs):
      self.fanId = fanId
      self.driver = driver
      self.led = led
      self.__dict__.update(kwargs)

   def getName(self):
      return 'fan%s' % self.fanId

   def getSpeed(self):
      return self.driver.getFanSpeed(self)

   def setSpeed(self, speed):
      return self.driver.setFanSpeed(self, speed)

   def getPresence(self):
      return self.driver.getFanPresence(self)

   def getStatus(self):
      return self.driver.getFanStatus(self)

   def getDirection(self):
      return self.driver.getFanDirection(self)

   def getLed(self):
      return self.led
