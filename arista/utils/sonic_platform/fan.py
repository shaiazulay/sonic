#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.fan_base import FanBase
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Fan(FanBase):
   """
   Platform-specific Fan class

   Unimplemented methods:
   - get_model
   - get_serial
   """

   DEFAULT_TOLERANCE = 100

   fanDirectionConversion = {
      'forward': FanBase.FAN_DIRECTION_INTAKE,
      'reverse': FanBase.FAN_DIRECTION_EXHAUST,
   }

   def __init__(self, fan):
      self._target_speed = None
      self._fan = fan

   def get_id(self):
      return self._fan.getId()

   def get_name(self):
      return self._fan.getName()

   def get_direction(self):
      return self.fanDirectionConversion[self._fan.getDirection()]

   def get_speed(self):
      return self._fan.getSpeed()

   def get_target_speed(self):
      if self._target_speed is not None:
         return self._target_speed
      # Fallback, no target speed set
      return self.get_speed()

   def set_speed(self, speed):
      self._target_speed = speed
      return self._fan.setSpeed(speed)

   def get_speed_tolerance(self):
      try:
         return self._fan.getSpeedTolerance()
      except AttributeError:
         return self.DEFAULT_TOLERANCE

   def set_status_led(self, color):
      try:
         self._fan.getLed().setColor(color)
         return True
      except (IOError, OSError, ValueError):
         return False

   def get_status_led(self):
      return self._fan.getLed().getColor()

   def get_status(self):
      return self._fan.getStatus()

   def get_presence(self):
      return self._fan.getPresence()

   def get_interrupt_file(self):
      return None
