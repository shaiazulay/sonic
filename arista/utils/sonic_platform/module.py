#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.module_base import ModuleBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Module(ModuleBase):
   """
   Platform-specific class for interfacing with a module
   (supervisor module, line card module, etc. applicable for a modular chassis)
   """
   pass
