import logging

from contextlib import closing

from ..core.driver import Driver
from ..core import utils

class Ds460I2cDriver(Driver):
   def __init__(self, name=None, addr=None, **kwargs):
      self.name = name
      self.addr = addr
      super(Ds460I2cDriver, self).__init__(*kwargs)

   def setup(self):
      addr = self.addr.address

      logging.debug('%s: initializing registers', self.name)
      with closing(utils.SMBus(self.addr.bus)) as bus:
         for _ in utils.Retrying(interval=10.0, delay=0.5):
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

      super(Ds460I2cDriver, self).setup()
