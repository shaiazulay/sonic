from __future__ import print_function, with_statement

import logging
import os

from ..core.driver import Driver
from ..core.inventory import Xcvr
from ..core.utils import inSimulation, FileWaiter

class SysfsDriver(Driver):
   def __init__(self, sysfsPath=None, **kwargs):
      self.sysfsPath = sysfsPath
      super(SysfsDriver, self).__init__(**kwargs)

   def __str__(self):
      return '%s(path=%s)' % (self.__class__.__name__, self.sysfsPath)

   def read(self, name):
      with open(os.path.join(self.sysfsPath, name), 'r') as f:
         return f.read().rstrip()

   def write(self, name, value):
      if inSimulation():
         return None
      with open(os.path.join(self.sysfsPath, name), 'w') as f:
         return f.write(value)

class PsuSysfsDriver(SysfsDriver):
   def getPsuPresence(self, psu):
      return self.read('psu%d_%s' % (psu.psuId, 'present')) == '1'

   def getPsuStatus(self, psu):
      if psu.statusGpio:
         return self.read('psu%d_%s' % (psu.psuId, 'status')) == '1'
      return self.getPsuPresence(psu)

class XcvrSysfsDriver(SysfsDriver):
   def getXcvrPresence(self, xcvr):
      return self.read('%s_%s' % (xcvr.name, 'present')) == '1'

   def getXcvrLowPowerMode(self, xcvr):
      if xcvr.xcvrType == Xcvr.SFP:
         return False
      return self.read('%s_%s' % (xcvr.name, 'lp_mode')) == '1'

   def setXcvrLowPowerMode(self, xcvr, value):
      if xcvr.xcvrType == Xcvr.SFP:
         return False
      return self.write('%s_%s' % (xcvr.name, 'lp_mode'), '1' if value else '0')

   def getXcvrModuleSelect(self, xcvr):
      if xcvr.xcvrType == Xcvr.SFP:
         return True
      return self.read('%s_%s' % (xcvr.name, 'modsel')) == '1'

   def setXcvrModuleSelect(self, xcvr, value):
      if xcvr.xcvrType == Xcvr.SFP:
         return True
      logging.debug('setting modsel for %s to %s', xcvr.name, value)
      return self.write('%s_%s' % (xcvr.name, 'modsel'), '1' if value else '0')

   def getXcvrTxDisable(self, xcvr):
      if xcvr.xcvrType == Xcvr.SFP:
         return self.read('%s_%s' % (xcvr.name, 'txdisable')) == '1'
      return False

   def setXcvrTxDisable(self, xcvr, value):
      if xcvr.xcvrType == Xcvr.SFP:
         logging.debug('setting txdisable for %s to %s', xcvr.name, value)
         return self.write('%s_%s' % (xcvr.name, 'txdisable'), '1' if value else '0')
      return False

class ResetSysfsDriver(SysfsDriver):
   def readReset(self, reset):
      return self.read('%s_%s' % (reset.name, 'reset'))

   def resetComponentIn(self, reset):
      logging.debug('putting %s in reset', reset.name)
      return self.write('%s_%s' % (reset.name, 'reset'), 1)

   def resetComponentOut(self, reset):
      logging.debug('putting %s out of reset', reset.name)
      return self.write('%s_%s' % (reset.name, 'reset'), 0)

class FanSysfsDriver(SysfsDriver):
   def __init__(self, maxPwm=None, waitFile=None, waitTimeout=None, **kwargs):
      self.maxPwm = maxPwm
      self.fileWaiter = FileWaiter(waitFile, waitTimeout)
      super(FanSysfsDriver, self).__init__(**kwargs)

   def setup(self):
      super(FanSysfsDriver, self).setup()
      self.fileWaiter.waitFileReady()

   # Fan speeds are a percentage
   def getFanSpeed(self, fan):
      return int(float(self.read('pwm%s' % fan.fanId)) / self.maxPwm * 100)

   def setFanSpeed(self, fan, speed):
      if not int(speed) in range(101):
         logging.error('invalid speed setting %s for fan %s', speed, fan.fanId)
         return None
      logging.debug('setting fan %s speed to %s', fan.fanId, speed)
      return self.write('pwm%s' % fan.fanId,
                        str(int(int(speed) * 0.01 * self.maxPwm)))

   def getFanDirection(self, fan):
      return self.read('fan%s_airflow' % fan.fanId)
