from __future__ import with_statement

import logging
from collections import namedtuple

from ..core.driver import Driver
from ..core.inventory import ReloadCause
from ..core.utils import SMBus, inSimulation

from .common import I2cComponent

UcdGpi = namedtuple( 'UcdGpi', [ 'bit' ] )
UcdMon = namedtuple( 'UcdMon', [ 'val' ] )

class UcdReloadCause(ReloadCause):
   def __init__(self, name):
      self.name = name

   def reason(self):
      return self.name

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

   def dumpReg(self, name, data):
      logging.debug('%s reg: %s', name, ' '.join('%02x' % s for s in data))

   def getBlock(self, reg):
      size = self.bus.read_byte_data(self.addr, reg)
      return self.bus.read_i2c_block_data(self.addr, reg, size + 1)

   def getVersion(self):
      if inSimulation():
         return "SERIAL UCDSIM 2.3.4.0005 241218"
      data = self.getBlock(self.component.MFR_SERIAL)
      serial = ''.join(chr(c) for c in data[1:data[0]+1])
      data = self.getBlock(self.component.DEVICE_ID)
      devid = ''.join(chr(c) for c in data[1:data[0]+1] if c).replace('|', ' ')
      return '%s %s' % (serial, devid)

   def readFaults(self, reg=None):
      if inSimulation():
         return [ 0 ] * 12
      reg = reg or self.component.LOGGED_FAULTS
      size = self.bus.read_byte_data(self.addr, reg)
      res = self.bus.read_i2c_block_data(self.addr, reg, size + 1)
      if reg == self.component.LOGGED_FAULTS:
         self.dumpReg('fault', res)
      return res

   def clearFaults(self):
      if inSimulation():
         return
      reg = self.component.LOGGED_FAULTS
      size = self.bus.read_byte_data(self.addr, reg)
      data = [ size ] + [ 0 ] * size
      self.bus.write_i2c_block_data(self.addr, reg, data)

   def getFaultCount(self):
      if inSimulation():
         return 0
      reg = self.component.LOGGED_FAULT_DETAIL_INDEX
      res = self.bus.read_word_data(self.addr, reg)
      return res >> 8

   def getFaultNum(self, num):
      if inSimulation():
         return [ 0 ] * 12
      self.bus.write_word_data(self.addr,
                               self.component.LOGGED_FAULT_DETAIL_INDEX, num)
      res = self.readFaults(self.component.LOGGED_FAULT_DETAIL)
      self.dumpReg('fault %d' % num, res)
      return res

class Ucd(I2cComponent):

   LOGGED_FAULTS = 0xea
   LOGGED_FAULT_DETAIL_INDEX = 0xeb
   LOGGED_FAULT_DETAIL = 0xec

   MFR_SERIAL = 0x9e
   DEVICE_ID = 0xfd

   hasGpi = True
   faultValueSize = 2

   def __init__(self, addr, causes=None, **kwargs):
      super(Ucd, self).__init__(addr, **kwargs)
      self.addDriver(UcdI2cDevDriver)
      self.causes = causes or {}

   def setup(self):
      with self.drivers[0] as drv:
         try:
            serial = drv.getVersion()
            logging.info('%s version: %s', self, serial)
         except Exception:
            logging.error('%s: failed to version information', self)

   def _getGpiFaults(self, reg):
      causes = []
      for name, typ in self.causes.items():
         if not isinstance(typ, UcdGpi):
            continue
         if reg & (1 << (typ.bit - 1)):
            causes.append(UcdReloadCause(name))
      return causes

   def _getFaultNum(self, reg):
      causes = []
      msecs = reg[1] << 24 | reg[2] << 16 | reg[3] << 8 | reg[4]
      fid = reg[5] << 24 | reg[6] << 16 | reg[7] << 8 | reg[8]
      paged = (fid >> 31) & 0x1
      ftype = (fid >> 27) & 0xf
      page = ((fid >> 23) & 0xf) + 1
      days = fid & 0x7fffff
      value = reg[10] << 8 | reg[9]
      logging.debug('paged=%d type=%d page=%d days=%d msecs=%d value=0x%04x',
                    paged, ftype, page, days, msecs, value)

      if not paged and ftype == 9:
         # this is a Gpi
         for name, typ in self.causes.items():
            if isinstance(typ, UcdGpi) and typ.bit == page:
               logging.debug('found: %s', name)
               causes.append(UcdReloadCause(name))
      elif paged and ftype in [ 0, 1 ]:
         # this is a Mon
         for name, typ in self.causes.items():
            if isinstance(typ, UcdMon) and typ.val == page:
               logging.debug('found: %s', name)
               causes.append(UcdReloadCause(name))
      else:
         logging.debug('unknown cause')
         causes.append(UcdReloadCause('unknown'))

      return causes

   def _getReloadCauses(self, drv):
      reg = drv.readFaults()
      if reg[ 1 ]:
         logging.debug('some non paged faults were detected')

      causes = []
      if self.hasGpi:
         causes = self._getGpiFaults(reg[ 2 ])
         logging.debug('found %d gpi faults', len(causes))
         for cause in causes:
            logging.debug('found: %s', cause)

      faultCount = drv.getFaultCount()
      logging.debug('found %d faults', faultCount)
      for i in range(0, faultCount):
         causes.extend(self._getFaultNum(drv.getFaultNum(i)))

      return causes

   def getReloadCauses(self, clear=False):
      if not self.causes:
         return []

      with self.drivers[0] as drv:
         causes = self._getReloadCauses(drv)
         if clear:
            logging.debug('clearing faults')
            drv.clearFaults()

      return causes

class Ucd90160(Ucd):
   pass

class Ucd90120(Ucd):
   hasGpi = False

class Ucd90120A(Ucd):
   pass

class Ucd90320(Ucd):
   hasGpi = False
