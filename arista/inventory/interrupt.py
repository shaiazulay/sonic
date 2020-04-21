
from . import InventoryInterface

class Interrupt(InventoryInterface):
   def set(self):
      raise NotImplementedError()

   def clear(self):
      raise NotImplementedError()

   def getFile(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         # TODO: get ?
         "file": self.getFile(),
      }
