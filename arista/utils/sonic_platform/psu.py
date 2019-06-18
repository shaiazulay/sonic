#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.psu_base import PsuBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Psu(PsuBase):
   """Platform-specific PSU class"""

   def __init__(self, psu):
      self.psu_ = psu
