import logging
import os.path
import time

from contextlib import closing

from ..core.utils import Retrying, SMBus, simulateWith

from .common import I2cKernelComponent

class Ds460(I2cKernelComponent):
   def __init__(self, addr, hwmonDir, **kwargs):
      # pmbus if dps460 is not available
      super(Ds460, self).__init__(addr, 'dps460',
                                  waitFile=hwmonDir,
                                  **kwargs)
      self.hwmonDir = hwmonDir

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

   def setup(self):
      addr = self.addr.address

      logging.debug('initializing ds460 registers')
      with closing(SMBus(self.addr.bus)) as bus:
         for _ in Retrying(interval=10.0, delay=0.5):
            try:
               bus.read_byte_data(addr, 0x00)
               logging.debug('ds460: device accessible: bus={}'.format(self.addr.bus))
               break
            except IOError:
               logging.debug('ds460: device not accessible; retrying...')
         else:
            logging.error('ds460: failed to access device: bus={}'.format(self.addr.bus))
            return

         try:
            byte = bus.read_byte_data(addr, 0x10)
            bus.write_byte_data(addr, 0x10, 0)
            bus.write_byte_data(addr, 0x03, 1)
            bus.write_byte_data(addr, 0x10, byte)
         except IOError:
            logging.debug('ds460: failed to initialize')

      super(Ds460, self).setup()
