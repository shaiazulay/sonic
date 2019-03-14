from __future__ import print_function, with_statement

from ..core.inventory import Psu

class PsuImpl(Psu):
   def __init__(self, **kwargs):
      self.statusGpio = True
      self.__dict__.update(kwargs)

   def getPresence(self):
      return self.driver.getPsuPresence(self)

   def getStatus(self):
      return self.driver.getPsuStatus(self)
