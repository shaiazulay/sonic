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
