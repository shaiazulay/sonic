from __future__ import with_statement

import datetime
import logging
import re
from collections import namedtuple

from ..core.config import Config
from ..core.driver import Driver
from ..core.inventory import ReloadCause
from ..core.utils import SMBus, JsonStoredData, inSimulation

from .common import I2cComponent

UcdGpi = namedtuple( 'UcdGpi', [ 'bit' ] )
UcdMon = namedtuple( 'UcdMon', [ 'val' ] )

class UcdReloadCause(ReloadCause):
   def __init__(self, name=None, time=None):
      self.name = name
      self.time = time

   def reason(self):
      return '%s%s' % (self.name, ', time: %s' % self.time if self.time else '')

   def getName(self):
      return self.name

   def getTime(self):
      return self.time

   def setName(self, name):
      self.name = name

   def setTime(self, time):
      self.time = time

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
   RUN_TIME_CLOCK = 0xd7
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
      self.oldestTime = datetime.datetime(1970, 1, 1)

   def setup(self):
      with self.drivers[0] as drv:
         try:
            serial = drv.getVersion()
            logging.info('%s version: %s', self, serial)
         except Exception:
            logging.error('%s: failed to version information', self)

         # DPM run time clock needs to be updated
         try:
            self._setRunTimeClock(drv)
            logging.info('%s time: %s', self, self._getRunTimeClock(drv))
         except Exception:
            logging.error('%s: failed to set run time clock', self)

         self.getReloadCauses(clear=True)

   def _setRunTimeClock(self, drv):
      size = drv.bus.read_byte_data(self.addr.address, self.RUN_TIME_CLOCK)
      diff = datetime.datetime.now() - self.oldestTime
      msecsInt = int(diff.seconds * 1000 + diff.microseconds / 1000)
      daysInt = diff.days
      msecsByte1 = (msecsInt >> 24) & 0xff
      msecsByte2 = (msecsInt >> 16) & 0xff
      msecsByte3 = (msecsInt >> 8) & 0xff
      msecsByte4 = msecsInt & 0xff
      daysByte1 = (daysInt >> 24) & 0xff
      daysByte2 = (daysInt >> 16) & 0xff
      daysByte3 = (daysInt >> 8) & 0xff
      daysByte4 = daysInt & 0xff
      data = [size, msecsByte1, msecsByte2, msecsByte3, msecsByte4,
              daysByte1, daysByte2, daysByte3, daysByte4]
      drv.bus.write_i2c_block_data(self.addr.address, self.RUN_TIME_CLOCK, data)

   def _getRunTimeClock(self, drv):
      size = drv.bus.read_byte_data(self.addr.address, self.RUN_TIME_CLOCK)
      res = drv.bus.read_i2c_block_data(self.addr.address, self.RUN_TIME_CLOCK,
                                        size+1)
      msecs = res[4] | (res[3] << 8) | (res[2] << 16) | (res[1] << 24)
      days = res[8] | (res[7] << 8) | (res[6] << 16) | (res[5] << 24)
      return self.oldestTime + datetime.timedelta(days=days, milliseconds=msecs)

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
      days = int(days)
      secs = int(msecs / 1000)
      usecs = int((msecs - secs * 1000) * 1000)
      time = self.oldestTime + datetime.timedelta(days=days, seconds=secs,
                                                  microseconds=usecs)
      logging.debug('paged=%d type=%d page=%d value=0x%04x time=%s',
                    paged, ftype, page, value, time)

      if not paged and ftype == 9:
         # this is a Gpi
         for name, typ in self.causes.items():
            if isinstance(typ, UcdGpi) and typ.bit == page:
               logging.debug('found: %s', name)
               causes.append(UcdReloadCause(name, str(time)))
      elif paged and ftype in [ 0, 1 ]:
         # this is a Mon
         for name, typ in self.causes.items():
            if isinstance(typ, UcdMon) and typ.val == page:
               logging.debug('found: %s', name)
               causes.append(UcdReloadCause(name, str(time)))
      else:
         logging.debug('unknown cause')
         causes.append(UcdReloadCause('unknown', str(time)))

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
      if not self.causes or inSimulation():
         return []

      rebootCauses = JsonStoredData('%s_%s' % (Config().reboot_cause_file, self.addr))
      if not rebootCauses.exist():
         with self.drivers[0] as drv:
            causes = self._getReloadCauses(drv)
            if clear:
               logging.debug('clearing faults')
               drv.clearFaults()
            if not causes:
               causes = [UcdReloadCause('unknown')]
         rebootCauses.writeList(causes)

      return rebootCauses.readList(UcdReloadCause)

class Ucd90160(Ucd):
   pass

class Ucd90120(Ucd):
   hasGpi = False

class Ucd90120A(Ucd):
   pass

class Ucd90320(Ucd):
   hasGpi = False
