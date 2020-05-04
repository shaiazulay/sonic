
from . import InventoryInterface

class Led(InventoryInterface):
   def getColor(self):
      raise NotImplementedError()

   def setColor(self, color):
      raise NotImplementedError()

   def getName(self):
      raise NotImplementedError()

   def isStatusLed(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "name": self.getName(),
         "color": self.getColor() if ctx.performIo else None,
         "is_status": self.isStatusLed(),
      }
