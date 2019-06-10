
from .common import I2cComponent
from ..core.prefdl import decodeBuffer
from ..drivers.eeprom import SeepromI2cDevDriver, EepromKernelDriver

class I2cEeprom(I2cComponent):
   def __init__(self, addr, name=None, drivers=None, **kwargs):
      drivers = drivers or [EepromKernelDriver(addr=addr)]
      super(I2cEeprom, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.name = name

   def read(self):
      return self.drivers['EepromKernelDriver'].read()

class I2cSeeprom(I2cComponent):
   def __init__(self, addr, name=None, drivers=None, **kwargs):
      drivers = drivers or [SeepromI2cDevDriver(addr=addr)]
      super(I2cSeeprom, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.name = name

   def read(self):
      return self.drivers['SeepromI2cDevDriver'].read()

class PrefdlSeeprom(I2cSeeprom):
   def prefdl(self):
      data = self.read()
      return decodeBuffer(data[8:]).data()

