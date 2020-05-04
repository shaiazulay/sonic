
from . import InventoryInterface

class Fan(InventoryInterface):
   def getName(self):
      raise NotImplementedError()

   def getSpeed(self):
      raise NotImplementedError()

   def setSpeed(self, speed):
      raise NotImplementedError()

   def getDirection(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "name": self.getName(),
         "speed": self.getSpeed() if ctx.performIo else None,
         "direction": self.getDirection() if ctx.performIo else None,
      }
