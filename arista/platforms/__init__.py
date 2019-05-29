
import os

def getPlatformModules():
   platformPath = os.path.dirname(__file__)
   modules = []

   for root, _, files in os.walk(platformPath):
      root = root[len(platformPath)+1:]
      for f in files:
         if not f.endswith('.py') or f == '__init__.py':
            continue
         module = os.path.join(root, f[:-3]).replace('/', '.')
         modules.append(module)

   return modules

__all__ = getPlatformModules()

# NOTE: this import relies on __all__ and therefore has to be here
from . import * # pylint: disable=wildcard-import,wrong-import-position
