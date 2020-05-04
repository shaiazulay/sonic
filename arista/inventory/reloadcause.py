
from . import InventoryInterface

class ReloadCause(InventoryInterface):
   def getTime(self):
      raise NotImplementedError()

   def getCause(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "time": self.getTime(),
         "cause": self.getCause(),
      }
