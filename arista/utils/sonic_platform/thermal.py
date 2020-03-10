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

   def __init__(self, temp):
      self._temp = temp

   def get_temperature(self):
      return self._temp.getTemperature()

   def get_low_threshold(self):
      return self._temp.getLowThreshold()

   def set_low_threshold(self, temperature):
      try:
         self._temp.setLowThreshold(temperature)
         return True
      except (IOError, OSError, ValueError):
         return False

   def get_high_threshold(self):
      return self._temp.getHighThreshold()

   def set_high_threshold(self, temperature):
      try:
         self._temp.setHighThreshold(temperature)
         return True
      except (IOError, OSError, ValueError):
         return False
