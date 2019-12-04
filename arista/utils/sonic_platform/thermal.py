#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.thermal_base import ThermalBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Thermal(ThermalBase):
   """
   Platform-specific class for interfacing with a thermal module
   """
   pass
