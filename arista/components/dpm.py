from __future__ import with_statement

import logging

from ..core.driver import Driver
from ..core.utils import SMBus

from .common import I2cComponent

class UcdI2cDevDriver(Driver):
   def __init__(self, ucd):
      super(UcdI2cDevDriver, self).__init__(ucd)
      self.bus = None
      self.addr = ucd.addr.address

   def __enter__(self):
      self.bus = SMBus(self.component.addr.bus)
      return self

   def __exit__(self, *args):
      self.bus.close()

   def getBlock(self, reg):
      size = self.bus.read_byte_data(self.addr, reg)
      return self.bus.read_i2c_block_data(self.addr, reg, size + 1)

   def getVersion(self):
      data = self.getBlock(self.component.MFR_SERIAL)
      serial = ''.join(chr(c) for c in data[1:data[0]+1])
      data = self.getBlock(self.component.DEVICE_ID)
      devid = ''.join(chr(c) for c in data[1:data[0]+1] if c).replace('|', ' ')
      return '%s %s' % (serial, devid)

class Ucd(I2cComponent):

   MFR_SERIAL = 0x9e
   DEVICE_ID = 0xfd

   def __init__(self, addr, **kwargs):
      super(Ucd, self).__init__(addr, **kwargs)
      self.addDriver(UcdI2cDevDriver)

   def setup(self):
      with self.drivers[0] as drv:
         try:
            serial = drv.getVersion()
            logging.info('%s version: %s', self, serial)
         except:
            logging.error('%s: failed to version information', self)

class Ucd90160(Ucd):
   pass

class Ucd90120(Ucd):
   pass

class Ucd90120A(Ucd):
   pass

