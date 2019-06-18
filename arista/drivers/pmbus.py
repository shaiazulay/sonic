import logging
import os

from ..core.driver import Driver
from ..core.utils import simulateWith

class PmbusDriver(Driver):
   def __init__(self, addr=None, hwmonDir=None, sensors=None, **kwargs):
      self.addr = addr
      self.hwmonDir = hwmonDir
      self.sensors = sensors or []
      super(PmbusDriver, self).__init__(**kwargs)

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
      for sensor in self.sensors:
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
