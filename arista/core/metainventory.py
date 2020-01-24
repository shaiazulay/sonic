import copy

from .inventory import Inventory

_TEMPLATE_INVENTORY = Inventory()

class LazyInventory(Inventory):
   def __init__(self):
      pass

   def __getattr__(self, key):
      if not hasattr(_TEMPLATE_INVENTORY, key):
         raise AttributeError

      value = copy.deepcopy(getattr(_TEMPLATE_INVENTORY, key))
      setattr(self, key, value)
      return value

class MetaInventory(object):
   def __init__(self, invs=None):
      self.invs = invs or []

   def __getattr__(self, key):
      func = getattr(Inventory, key)
      def callback():
         data = None
         count = 0
         for inv in self.invs:
            res = func(inv)
            if data is None:
               data = type(res)()
            if isinstance(res, dict):
               data.update(res)
            elif isinstance(res, list):
               data.extend(res)
            elif isinstance(res, int):
               data += res
            else:
               raise ValueError('Unknown type to process')
            count += 1
         if count == 0:
            return copy.deepcopy(getattr(_TEMPLATE_INVENTORY, key)())
         return data
      return callback
