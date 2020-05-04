
from . import InventoryInterface

class Reset(InventoryInterface):
   def read(self):
      raise NotImplementedError()

   def resetIn(self):
      raise NotImplementedError()

   def resetOut(self):
      raise NotImplementedError()

   def getName(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "name": self.getName(),
         "value": self.read() if ctx.performIo else None,
      }
