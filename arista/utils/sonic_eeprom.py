"""
This file provides helper for sonic environment

Currently all arista switches have their eeprom at the same address and use
the same data format. Since it is not an open standard and all our platforms
need this having everything at the same place is easier.

The eeprom plugin end up being just the following

   import arista.utils.sonic_eeprom
   board = arista.utils.sonic_eeprom.getTlvInfoDecoder()

We should be able to remove "getTlvInfoDecoder" after we change it on
sonic-buildimage, and do:

   from arista.utils.sonic_eeprom import board
"""

from __future__ import absolute_import

import StringIO

from ..core import prefdl
from ..core.platform import fmted_prefdl_path, readPrefdl

try:
   from sonic_eeprom import eeprom_base
except ImportError as error:
   raise ImportError("%s - required module not found" % error)

class board(eeprom_base.EepromDecoder):
   def __init__(self, name, path, cpld_root, ro):
      self._prefdl_cache = {}
      self.prefdl_path = fmted_prefdl_path
      super(board, self).__init__(self.prefdl_path, None, 0, '', True)

   def read_eeprom(self):
      return str( readPrefdl() )

   def _decode_eeprom(self, e):
      pfdl = self._prefdl_cache.get(e, None)
      if pfdl is not None:
         return pfdl

      pfdl = prefdl.PreFdlFromFile(StringIO.StringIO(e))
      self._prefdl_cache[e] = pfdl

      return pfdl

   def decode_eeprom(self, e):
      pfdl = self._decode_eeprom(e)
      return pfdl.show()

   def is_checksum_valid(self, e):
      pfdl = self._decode_eeprom(e)
      return (True, pfdl.getCrc())

   def serial_number_str(self, e):
      pfdl = self._decode_eeprom(e)
      return pfdl.getField('SerialNumber')

   def mgmtaddrstr(self, e):
      pfdl = self._decode_eeprom(e)
      return pfdl.getField('MAC')

   def get_eeprom_dict(self, e):
      pfdl = self._decode_eeprom(e)
      return {'Data': pfdl.data()}

def getTlvInfoDecoder():
   return board
