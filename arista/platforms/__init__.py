
from collections import namedtuple
import importlib
import pkgutil
import sys

ModuleInfo = namedtuple('ModuleInfo', 'module_finder name ispkg')

def iter_modules2(path=None, prefix=''):
   """Starting from python3.6 iter_modules returns a the above namedtuple"""
   for module_loader, name, ispkg in pkgutil.iter_modules(path, prefix):
      yield ModuleInfo(module_loader, name, ispkg)

iter_modules = iter_modules2 if sys.version_info < (3, 6) else pkgutil.iter_modules

def walk_packages(path=None, prefix='', onerror=None):
   """Implementation from https://github.com/python/cpython/pull/11956"""
   def seen(p, m={}): # pylint: disable=dangerous-default-value
      if p in m:
         return True
      m[p] = True
      return False

   for info in iter_modules(path, prefix):
      yield info

      if info.ispkg:
         loader = info.module_finder.find_module(info.name)
         try:
            module = loader.load_module(info.name)
         except ImportError:
            if onerror is not None:
               onerror(info.name)
         except Exception: # pylint: disable=broad-except
            if onerror is not None:
               onerror(info.name)
            else:
               raise
         else:
            path = module.__path__

            # don't traverse path items we've seen before
            path = [p for p in path if not seen(p)]

            for item in walk_packages(path, info.name+'.', onerror):
               yield item

def importSubmodules(package, recursive=True):
   if isinstance(package, str):
      package = importlib.import_module(package)

   modules = {}
   for info in walk_packages(package.__path__):
      fullName = '%s.%s' % (package.__name__, info.name)
      modules[fullName] = importlib.import_module(fullName)
      if recursive and info.ispkg:
         modules.update(importSubmodules(fullName))

   return modules

__all__ = importSubmodules(__package__).keys()
