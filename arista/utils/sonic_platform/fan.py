#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.fan_base import FanBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Fan(FanBase):
   """Platform-specific Fan class"""

   fanDirectionConversion = {
      'forward': FanBase.FAN_DIRECTION_INTAKE,
      'reverse': FanBase.FAN_DIRECTION_EXHAUST,
   }

   def __init__(self, fan):
      self._fan = fan

   def get_name(self):
      return self._fan.getName()

   def get_direction(self):
      return self.fanDirectionConversion[self._fan.getDirection()]

   def get_speed(self):
      return self._fan.getSpeed()

   def set_speed(self, speed):
      return self._fan.setSpeed(speed)

   def set_status_led(self, color):
      try:
         self._fan.getLed().setColor(color)
         return True
      except (IOError, OSError, ValueError):
         return False

   def get_status(self):
      led = self._fan.getLed()
      return led.getColor() == self.STATUS_LED_COLOR_GREEN

   def get_presence(self):
      return self.get_status()

   def get_interrupt_file(self):
      return None
