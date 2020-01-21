
from __future__ import absolute_import, division, print_function

from collections import namedtuple, OrderedDict
from ...core.dynload import importSubmodules

Parser = namedtuple('Parser', ['name', 'func', 'parent', 'kwargs'])

registeredParsers = OrderedDict()

def registerParser(name, parent=None, **kwargs):
   '''Arguments to provide to a subparser'''
   def decorator(func):
      registeredParsers[name] = Parser(name, func, parent, kwargs)
      return func
   return decorator

def getParsers():
   return registeredParsers.values()

def getParser(name):
   return registeredParsers[name]

# dynamically load all parsers
__all__ = importSubmodules(__package__).keys()
