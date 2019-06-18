import logging

from contextlib import closing

from ..core.utils import Retrying, SMBus
from .common import I2cComponent
from ..drivers.i2c import I2cKernelDriver
from ..drivers.pmbus import PmbusDriver

class Ds460(I2cComponent):
   def __init__(self, addr, hwmonDir, name='dps460', drivers=None, priority=None,
                waitTimeout=None, **kwargs):
      self.name = name
      sensors = ['curr1', 'curr2', 'curr3', 'in1', 'in2']
      if not drivers:
         drivers = [I2cKernelDriver(name=name, addr=addr, waitFile=hwmonDir,
                                    waitTimeout=waitTimeout),
                    PmbusDriver(addr=addr, hwmonDir=hwmonDir, sensors=sensors)]
      super(Ds460, self).__init__(addr=addr, name=name, drivers=drivers,
                                  **kwargs)

   def getStatus(self):
      return self.drivers['PmbusDriver'].getStatus()

   def setup(self):
      addr = self.addr.address

      logging.debug('initializing %s registers', self.name)
      with closing(SMBus(self.addr.bus)) as bus:
         for _ in Retrying(interval=10.0, delay=0.5):
            try:
               bus.read_byte_data(addr, 0x00)
               logging.debug('%s: device accessible: bus=%s',
                             self.name, self.addr.bus)
               break
            except IOError:
               logging.debug('%s: device not accessible; retrying...', self.name)
         else:
            logging.error('%s: failed to access device: bus=%s',
                          self.name, self.addr.bus)
            return

         try:
            byte = bus.read_byte_data(addr, 0x10)
            bus.write_byte_data(addr, 0x10, 0)
            bus.write_byte_data(addr, 0x03, 1)
            bus.write_byte_data(addr, 0x10, byte)
         except IOError:
            logging.debug('%s: failed to initialize', self.name)

      super(Ds460, self).setup()
