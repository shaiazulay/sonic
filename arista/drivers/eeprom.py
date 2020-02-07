
from contextlib import closing
import os

from ..core.driver import Driver
from ..core.utils import SMBus

from .i2c import I2cKernelDriver

class EepromKernelDriver(I2cKernelDriver):
   def __init__(self, name='eeprom', module='eeprom', **kwargs):
      super(EepromKernelDriver, self).__init__(name=name, module=module, **kwargs)

   def read(self):
      path = os.path.join(self.getSysfsPath(), 'eeprom')
      with open(path) as f:
         return f.read()

class SeepromI2cDevDriver(Driver):

   offset = 0
   length = 256
   header_size = 8

   def __init__(self, addr=None, **kwargs):
      super(SeepromI2cDevDriver, self).__init__(**kwargs)
      self.addr = addr

   def read(self):
      with closing(SMBus(self.addr.bus)) as bus:
         data = ''
         bus.write_byte_data(self.addr.address, 0x00, 0)

         header = []
         # consecutive byte read
         for _ in range(self.offset, self.header_size):
            header += [bus.read_byte(self.addr.address)]

         # The 32 bits at 0x4 indicates the length of the prefdl (including the
         # header)
         length = ((header[4] << 24) |
                   (header[5] << 16) |
                   (header[6] << 8) |
                    header[7])

         data += ''.join(map(chr, header))

         # consecutive byte read
         for _ in range(self.offset + self.header_size, length):
            data += chr(bus.read_byte(self.addr.address))
         return data
