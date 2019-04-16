
from .component import Component, Priority
from .inventory import Inventory
from .driver import KernelDriver

class FixedSystem(Component):
   def __init__(self, drivers=None, **kwargs):
      drivers = drivers or [KernelDriver(module='eeprom'),
                            KernelDriver(module='i2c-dev')]
      super(FixedSystem, self).__init__(drivers=drivers, **kwargs)
      self.inventory = Inventory()

   def setup(self, priority=Priority.DEFAULT):
      super(FixedSystem, self).setup()
      super(FixedSystem, self).finish(priority)

   def getInventory(self):
      return self.inventory

   def __str__(self):
      return '%s()' % self.__class__.__name__

