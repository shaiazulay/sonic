#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.chassis_base import ChassisBase
   from arista.core.platform import readPrefdl
   from arista.utils.sonic_platform.fan import Fan
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Chassis(ChassisBase):
   def __init__(self, inventory):
      self.prefdl_ = readPrefdl()
      self.inventory_ = inventory
      self._fan_list = []
      for fan in self.inventory_.getFans():
         self._fan_list.append(Fan(fan))
      ChassisBase.__init__(self)

   def get_base_mac(self):
      mac = self.prefdl_.getField("MAC")
      return mac

   def get_serial_number(self):
      serial = self.prefdl_.getField("SerialNumber")
      return serial
