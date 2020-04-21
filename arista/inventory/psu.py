
from . import InventoryInterface

class Psu(InventoryInterface):
   def getName(self):
      raise NotImplementedError()

   def getPresence(self):
      raise NotImplementedError()

   def getStatus(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "name": self.getName(),
         "present": self.getPresence() if ctx.performIo else None,
         "getStatus": self.getStatus() if ctx.performIo else None,
      }
