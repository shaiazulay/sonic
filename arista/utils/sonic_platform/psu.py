#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.psu_base import PsuBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Psu(PsuBase):
   """Platform-specific PSU class"""

   def __init__(self, psu):
      self._psu = psu

   def set_status_led(self, color):
      try:
         self._psu.getLed().setColor(color)
      except (IOError, OSError, ValueError):
         return False
      return True

   def get_status_led(self, color):
      try:
         if color != self._psu.getLed().getColor():
            return False
      except (IOError, OSError, ValueError):
         return False
      return True

   def get_status(self):
      return self.get_status_led(self.STATUS_LED_COLOR_GREEN)

   def get_presence(self):
      return self.get_status()

   def get_powergood_status(self):
      return self.get_status()
