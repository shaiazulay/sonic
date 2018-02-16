import os.path

from contextlib import closing

from ..core.inventory import Psu
from ..core.utils import simulateWith
from .common import I2cKernelComponent

class ScdPmbusPsu(Psu):
   def __init__(self, scd, pmbus):
      self.psuId = scd.psuId
      self.scd_ = scd
      self.pmbus_ = pmbus

   def getPresence(self):
      return self.scd_.getPresence()

   def getStatus(self):
      return self.pmbus_.getStatus()

class PmbusPsuComponent(I2cKernelComponent):
   def __init__(self, addr, hwmonDir, **kwargs):
      super(PmbusPsuComponent, self).__init__(addr, "pmbus", waitFile=hwmonDir, **kwargs)
      self.hwmonDir = hwmonDir

   def getStatus():
      return self.rw_.readValue('status') == '1'

   def sensorPath(self, name):
      return os.path.join(self.hwmonDir, name)

   def readSensor(self, name):
      path = self.sensorPath(name)
      if not os.path.exists(path):
         logging.info('hwmon sensor %s does not exist', path)
         return 0, False
      logging.debug('hwmon-read %s', path)
      with open(path, 'r') as f:
         return int(f.read()), True

   def getStatusSim_(self):
      logging.info('reading psu status from hwmon: %s', self.hwmonDir)
      return True

   @simulateWith(getStatusSim_)
   def getStatus(self):
      # At least one sensor is expected to exist, otherwise treat it as a failure.
      nonZero = False
      # Check input and output values of current and voltage are in the range.
      for sensor in ['curr1', 'curr2', 'curr3', 'in1', 'in2']:
         # The value must be non zero.
         value, exists = self.readSensor('%s_input' % sensor)
         if not exists:
            continue
         elif not value:
            return False
         nonZero = True

         # The value must be lower than its critical value.
         valueCrit, exists = self.readSensor('%s_crit' % sensor)
         if exists and valueCrit and value > valueCrit:
            return False

         # The value must be greater than its lowest allowed value.
         valueLCrit, exists = self.readSensor('%s_lcrit' % sensor)
         if exists and value < valueLCrit:
            return False

      return nonZero
