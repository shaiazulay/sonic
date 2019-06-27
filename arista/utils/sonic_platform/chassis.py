#!/usr/bin/env python

from __future__ import print_function

try:
   from sonic_platform_base.chassis_base import ChassisBase
   from arista.core import cause
   from arista.core.platform import readPrefdl
   from arista.utils.sonic_platform.fan import Fan
   from arista.utils.sonic_platform.psu import Psu
except ImportError as e:
   raise ImportError("%s - required module not found" % e)

class Chassis(ChassisBase):
   REBOOT_CAUSE_DICT = {
      'powerloss': ChassisBase.REBOOT_CAUSE_POWER_LOSS,
      'overtemp': ChassisBase.REBOOT_CAUSE_THERMAL_OVERLOAD_OTHER,
      'reboot': ChassisBase.REBOOT_CAUSE_NON_HARDWARE,
      'watchdog': ChassisBase.REBOOT_CAUSE_WATCHDOG,
   }
   def __init__(self, inventory):
      self._prefdl = readPrefdl()
      self._inventory = inventory
      self._fan_list = []
      for fan in self._inventory.getFans():
         self._fan_list.append(Fan(fan))
      self._psu_list = []
      for psu in self._inventory.getPsus():
         self._psu_list.append(Psu(psu))
      ChassisBase.__init__(self)

   def get_base_mac(self):
      mac = self._prefdl.getField("MAC")
      return mac

   def get_serial_number(self):
      serial = self._prefdl.getField("SerialNumber")
      return serial

   def get_reboot_cause(self):
      unknown = (ChassisBase.REBOOT_CAUSE_HARDWARE_OTHER, 'unknown cause')
      causes = cause.getReloadCause()
      for item in causes:
         reason = item.getCause()
         time = item.getTime()
         if reason != "unknown" and time != "unknown":
            retCause = self.REBOOT_CAUSE_DICT.get(reason,
                  ChassisBase.REBOOT_CAUSE_HARDWARE_OTHER)
            retDesc = str(item)
            return (retCause, retDesc)
      return unknown
