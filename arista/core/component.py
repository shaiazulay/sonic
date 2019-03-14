from __future__ import print_function
from collections import defaultdict, OrderedDict

from .utils import flatten

import os

DEFAULT_WAIT_TIMEOUT = 15
ASIC_YIELD_TIME = os.getenv( 'ASIC_YIELD_TIME', 2 )

class Priority:
   DEFAULT = 0
   BACKGROUND = 1

class Component(object):
   def __init__(self, priority=Priority.DEFAULT, **kwargs):
      self.components = defaultdict(list)
      self.drivers = OrderedDict()
      self.priority = priority
      self.__dict__.update(kwargs)
      self.params = kwargs.keys()

   def __str__(self):
      kwargs = ['%s=%s' % (k, getattr(self, k)) for k in self.params]
      return '%s(%s)' % (self.__class__.__name__, ', '.join(kwargs))

   def addComponents(self, components):
      assert all(isinstance(c, Component) for c in components)
      for component in components:
         component.priority = max(component.priority, self.priority)
         self.components[component.priority].append(component)
      return self

   def addComponent(self, component):
      assert isinstance(component, Component)
      component.priority = max(component.priority, self.priority)
      self.components[component.priority].append(component)
      return self

   def addDriver(self, driver, *args, **kwargs):
      if driver:
         drv = driver(*args, **kwargs)
         self.drivers[getattr(drv, 'driverName', None) or driver.__name__] = drv

   def setup(self):
      for driver in self.drivers.values():
         driver.setup()
      for driver in self.drivers.values():
         driver.finish()

   def finish(self, priority=Priority.DEFAULT):
      # underlying component are initialized recursively but require the parent to
      # be fully initialized
      for component in self.components[priority]:
         component.setup()
      for component in self.components[Priority.DEFAULT]:
         component.finish(priority)

   def refresh(self):
      for component in flatten(self.components.values()):
         component.refresh()
      for driver in self.drivers.values():
         driver.refresh()

   def clean(self):
      for component in flatten(self.components.values()):
         component.clean()
      for driver in reversed(self.drivers.values()):
         driver.clean()

   def resetIn(self):
      for component in flatten(self.components.values()):
         component.resetIn()
      for driver in reversed(self.drivers.values()):
         driver.resetIn()

   def resetOut(self):
      for driver in self.drivers.values():
         driver.resetOut()
      for component in flatten(self.components.values()):
         component.resetOut()

   def getReloadCauses(self, clear=False):
      causes = []
      for driver in self.drivers.values():
         causes.extend(driver.getReloadCauses(clear=clear))
      for component in flatten(self.components.values()):
         causes.extend(component.getReloadCauses(clear=clear))
      return causes

   def waitForIt(self, timeout=DEFAULT_WAIT_TIMEOUT):
      for component in flatten(self.components.values()):
         component.waitForIt(timeout)

   def _dumpDrivers(self, depth, prefix):
      if len(self.drivers) == 1:
         for driver in self.drivers.values():
            driver.dump(prefix=' => ')
      elif self.drivers:
         spacer = ' ' * (depth * 3)
         print('%s%sdrivers:' % (spacer, prefix))
         for driver in self.drivers.values():
            driver.dump(depth + 1)

   def _dumpNode(self, depth, prefix):
      depth += 1
      spacer = ' ' * (depth * 3)
      if self.drivers.values():
         self._dumpDrivers(depth, prefix)
      print('%s%scomponents:' % (spacer, prefix))
      for component in flatten(self.components.values()):
         component.dump(depth + 1)

   def dump(self, depth=0, prefix=' - '):
      spacer = ' ' * (depth * 3)
      end = '' if len(self.drivers) == 1 else '\n'
      print('%s%s%s' % (spacer, prefix,self), end=end)
      if self.components:
         self._dumpNode(depth, prefix)
      else:
         self._dumpDrivers(depth, prefix)

