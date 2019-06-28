#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.watchdog_base import WatchdogBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Watchdog(WatchdogBase):
   """Platform-specific watchdog class"""

   def __init__(self, watchdog):
      self.watchdog_ = watchdog
