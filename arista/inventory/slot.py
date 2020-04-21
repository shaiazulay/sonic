
from . import InventoryInterface

class Slot(InventoryInterface):
   def getPresence(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         # TODO: name ?
         "present": self.getPresence() if ctx.performIo else None,
      }
