import logging

from contextlib import closing

from ..core.driver import Driver
from ..core import utils

class UpperlakePsuDriver(Driver):
   def __init__(self, addr=None, **kwargs):
      # MSB: Description (Good/bad values)
      # 3:   PSU1 AC OK (1/0)
      # 2:   PSU2 AC OK (1/0)
      # 1:   PSU1 DC OK (1/0)
      # 0:   PSU2 DC OK (1/0)
      self.addr = addr
      super(UpperlakePsuDriver, self).__init__(**kwargs)

   def getPsuStatus(self, psu):
      statusMask = 0b1010 >> (psu.psuId - 1)
      reg = 0x0c
      logging.debug('i2c-read %d %#02x %#02x', self.addr.bus, self.addr.address, reg)

      # Both AC and DC status bits must be on.
      with closing(utils.SMBus(self.addr.bus)) as bus:
         state = bus.read_byte_data(self.addr.address, reg)
         logging.debug('psu state is %#02x', state)
         return state & statusMask == statusMask
