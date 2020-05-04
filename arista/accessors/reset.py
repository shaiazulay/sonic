from ..inventory.reset import Reset

class ResetImpl(Reset):
   def __init__(self, name=None, driver=None, **kwargs):
      self.name = name
      self.driver = driver
      self.__dict__.update(kwargs)

   def read(self):
      return self.driver.readReset(self)

   def resetIn(self):
      return self.driver.resetComponentIn(self)

   def resetOut(self):
      return self.driver.resetComponentOut(self)

   def getName(self):
      return self.name
