
from . import InventoryInterface

class Phy(InventoryInterface):
   def getReset(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "reset": self.getReset().__diag__(ctx),
      }
