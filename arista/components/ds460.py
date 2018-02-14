import logging

from contextlib import closing

from ..core.utils import SMBus

from .common import I2cKernelComponent

class Ds460(I2cKernelComponent):
   def __init__(self, addr, **kwargs):
      # pmbus if dps460 is not available
      super(Ds460, self).__init__(addr, 'dps460', **kwargs)

   def setup(self):
      addr = self.addr.address

      logging.debug('initializing ds460 registers')
      with closing(SMBus(self.addr.bus)) as bus:
         try:
            bus.read_byte_data(addr, 0x00)
         except IOError:
            logging.debug('device ds460 not found')
            return

         try:
            byte = bus.read_byte_data(addr, 0x10)
            bus.write_byte_data(addr, 0x10, 0)
            bus.write_byte_data(addr, 0x03, 1)
            bus.write_byte_data(addr, 0x10, byte)
         except IOError:
            logging.debug('failed to initialize ds460')

      super(Ds460, self).setup()


