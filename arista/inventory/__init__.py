
import warnings

class InventoryInterface(object):
   def __diag__(self, ctx):
      warnings.warn('inventory objects should implement diag', DeprecationWarning)
      return {}

   def genDiag(self, ctx):
      return {
         "version": 1,
         "name": self.__class__.__name__,
         "desc": self.desc.__diag__(ctx) if hasattr(self, 'desc') else {},
         "data": self.__diag__(ctx),
      }
