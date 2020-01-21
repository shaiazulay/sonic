
from __future__ import absolute_import, division, print_function

import logging
import importlib

from collections import namedtuple
from ..args import getParser

# from ...core.dynload import 

Action = namedtuple('Action', ['name', 'func', 'parent', 'needsPlatform'])

registeredActions = {}

def registerAction(*names, **kwargs):
   '''Register an action function for a subparser'''
   needsPlatform = kwargs.pop('needsPlatform', True)
   parent = kwargs.pop('parent', None)
   def decorator(func):
      for name in names:
         registeredActions[name] = Action(name, func, parent, needsPlatform)
      return func
   return decorator

def getAction(name):
   if name not in registeredActions:
      parser = getParser(name)
      module = parser.func.__module__
      actionModule = '.cli.actions.%s' % module[ module.rfind( '.' ) + 1: ]
      logging.debug( 'Loading action module %s', actionModule )
      importlib.import_module( actionModule, package='arista' )
   return registeredActions[name]
