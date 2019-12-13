from .cause import ReloadCauseEntry
from .component import Component, Priority
from .config import Config
from .inventory import Inventory
from .driver import KernelDriver
from .utils import inSimulation, JsonStoredData

class FixedSystem(Component):

   PLATFORM = None
   SID = None
   SKU = None

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

   def getReloadCauses(self, clear=False):
      if inSimulation():
         return []
      rebootCauses = JsonStoredData('%s' % Config().reboot_cause_file)
      if not rebootCauses.exist():
         causes = super(FixedSystem, self).getReloadCauses(clear=clear)
         rebootCauses.writeList(causes)
      return rebootCauses.readList(ReloadCauseEntry)
