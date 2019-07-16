#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.sfp_base import SfpBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Sfp(SfpBase):
   """Platform-specific sfp class"""

   def __init__(self, sfp):
      self._sfp = sfp

   def get_name(self):
      return self._sfp.getName()

   def get_presence(self):
      return self._sfp.getPresence()

   def clear_interrupt(self):
      intr = self._sfp.getInterruptLine()
      if not intr:
         return False
      self.get_presence()
      intr.clear()
      return True

   def get_interrupt_file(self):
      intr = self._sfp.getInterruptLine()
      return intr.getFile()
