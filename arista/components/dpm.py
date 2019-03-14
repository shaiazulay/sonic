from __future__ import with_statement

import datetime
import logging
import re
from collections import namedtuple

from ..core.config import Config
from ..core.inventory import ReloadCause
from ..core.utils import JsonStoredData, inSimulation

from ..drivers.dpm import UcdI2cDevDriver

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

class Ucd(I2cComponent):
   class Registers(object):
      RUN_TIME_CLOCK = 0xd7
      LOGGED_FAULTS = 0xea
      LOGGED_FAULT_DETAIL_INDEX = 0xeb
      LOGGED_FAULT_DETAIL = 0xec

      MFR_SERIAL = 0x9e
      DEVICE_ID = 0xfd

   gpiSize = 1
   faultValueSize = 2

   faultTimeBase = datetime.datetime(1970, 1, 1)
   daysOffset = 0

   def __init__(self, addr, causes=None, **kwargs):
      super(Ucd, self).__init__(addr, **kwargs)
      self.addDriver(UcdI2cDevDriver, self.Registers, addr)
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
      size = drv.bus.read_byte_data(self.addr.address, self.Registers.RUN_TIME_CLOCK)
      diff = datetime.datetime.now() - self.oldestTime
      msecsInt = int(diff.seconds * 1000 + diff.microseconds / 1000)
      daysInt = diff.days
      daysInt += self.daysOffset
      msecsByte1 = (msecsInt >> 24) & 0xff
      msecsByte2 = (msecsInt >> 16) & 0xff
      msecsByte3 = (msecsInt >> 8) & 0xff
      msecsByte4 = msecsInt & 0xff
      daysByte1 = (daysInt >> 24) & 0xff
      daysByte2 = (daysInt >> 16) & 0xff
      daysByte3 = (daysInt >> 8) & 0xff
      daysByte4 = daysInt & 0xff
      data = [msecsByte1, msecsByte2, msecsByte3, msecsByte4,
              daysByte1, daysByte2, daysByte3, daysByte4]
      drv.setBlock(self.Registers.RUN_TIME_CLOCK, [ len(data) ] + data)

   def _getRunTimeClock(self, drv):
      res = drv.getBlock(self.Registers.RUN_TIME_CLOCK)
      msecs = res[4] | (res[3] << 8) | (res[2] << 16) | (res[1] << 24)
      days = res[8] | (res[7] << 8) | (res[6] << 16) | (res[5] << 24)
      days -= self.daysOffset
      return self.oldestTime + datetime.timedelta(days=days, milliseconds=msecs)

   def _getGpiFaults(self, reg):
      causes = []
      for name, typ in self.causes.items():
         if not isinstance(typ, UcdGpi):
            continue
         if reg & (1 << (typ.bit - 1)):
            causes.append(UcdReloadCause(name))
      return causes

   def _parseFaultDetail(self, reg):
      msecs = (reg[1] << 24) | (reg[2] << 16) | (reg[3] << 8) | reg[4]
      fid = (reg[5] << 24) | (reg[6] << 16) | (reg[7] << 8) | reg[8]
      paged = (fid >> 31) & 0x1
      ftype = (fid >> 27) & 0xf
      page = ((fid >> 23) & 0xf) + 1
      days = fid & 0x7fffff
      value = (reg[10] << 8) | reg[9]
      return paged, ftype, page, value, days, msecs

   def _getFaultNum(self, reg):
      causes = []

      if len(reg) < 11:
         logging.debug('invalid unknown cause %s' % reg)
         causes.append(UcdReloadCause('unknown'))
         return causes

      paged, ftype, page, value, days, msecs = self._parseFaultDetail(reg)
      days = int(days)
      secs = int(msecs / 1000)
      usecs = int((msecs - secs * 1000) * 1000)

      time = self.faultTimeBase + datetime.timedelta(days=days, seconds=secs,
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
      if self.gpiSize:
         gpi = 0
         for i in range(0, self.gpiSize):
            gpi |= reg[ 2 + i ] << (8 * i)
         causes = self._getGpiFaults(gpi)
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
   gpiSize = 0

class Ucd90120A(Ucd):
   pass

class Ucd90320(Ucd):
   gpiSize = 4

   # The fault time is from 2000-01-01
   faultTimeBase = datetime.datetime(2000, 1, 1)
   # RUN_TIME_CLOCK is from 0001-01-01
   daysOffset = 719162    # Equals to 2000-01-01 - 0001-01-01

   def _parseFaultDetail(self, reg):
      pageAndMsecs = (reg[1] << 24) | (reg[2] << 16) | (reg[3] << 8) | reg[4]
      page = (pageAndMsecs >> 27) + 1
      msecs = pageAndMsecs & 0x7ffffff
      fid = (reg[5] << 24) | (reg[6] << 16) | (reg[7] << 8) | reg[8]
      paged = (fid >> 31) & 0x1
      ftype = (fid >> 27) & 0xf
      days = (fid >> 11) & 0xffff
      value = (reg[10] << 8) | reg[9]
      return paged, ftype, page, value, days, msecs
