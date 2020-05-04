
from . import InventoryInterface

class PowerCycle(InventoryInterface):
   def powerCycle(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {}
