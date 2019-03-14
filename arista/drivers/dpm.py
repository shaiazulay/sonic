import logging

from ..core.driver import Driver
from ..core.utils import inSimulation, SMBus

SMBUS_BLOCK_MAX_SZ = 32

class UcdI2cDevDriver(Driver):
   def __init__(self, registers, addr):
      super(UcdI2cDevDriver, self).__init__()
      self.bus = None
      self.registers = registers
      self.addr = addr

   def __enter__(self):
      self.bus = SMBus(self.addr.bus)
      return self

   def __exit__(self, *args):
      self.bus.close()

   def dumpReg(self, name, data):
      logging.debug('%s reg: %s', name, ' '.join('%02x' % s for s in data))

   # FIXME: the block read/write is truncated to 32 bytes for smbus support
   def getBlock(self, reg):
      size = self.bus.read_byte_data(self.addr.address, reg)
      return self.bus.read_i2c_block_data(self.addr.address, reg,
                                          min(size + 1, SMBUS_BLOCK_MAX_SZ))

   # FIXME: the block read/write is truncated to 32 bytes for smbus support
   def setBlock(self, reg, data):
      self.bus.write_i2c_block_data(self.addr.address, reg, data[:SMBUS_BLOCK_MAX_SZ])

   def getVersion(self):
      if inSimulation():
         return "SERIAL UCDSIM 2.3.4.0005 241218"
      data = self.getBlock(self.registers.MFR_SERIAL)
      serial = ''.join(chr(c) for c in data[1:data[0]+1])
      data = self.getBlock(self.registers.DEVICE_ID)
      devid = ''.join(chr(c) for c in data[1:data[0]+1] if c).replace('|', ' ')
      return '%s %s' % (serial, devid)

   def readFaults(self, reg=None):
      if inSimulation():
         return [ 0 ] * 12
      reg = reg or self.registers.LOGGED_FAULTS
      res = self.getBlock(reg)
      if reg == self.registers.LOGGED_FAULTS:
         self.dumpReg('fault', res)
      return res

   # FIXME: the block read/write is truncated to 32 bytes for smbus support
   def clearFaults(self):
      if inSimulation():
         return
      reg = self.registers.LOGGED_FAULTS
      size = self.bus.read_byte_data(self.addr.address, reg)
      size = min(size, SMBUS_BLOCK_MAX_SZ - 1)
      data = [ size ] + [ 0 ] * size
      self.setBlock(reg, data)

   def getFaultCount(self):
      if inSimulation():
         return 0
      reg = self.registers.LOGGED_FAULT_DETAIL_INDEX
      res = self.bus.read_word_data(self.addr.address, reg)
      return res >> 8

   def getFaultNum(self, num):
      if inSimulation():
         return [ 0 ] * 12
      self.bus.write_word_data(self.addr.address,
                               self.registers.LOGGED_FAULT_DETAIL_INDEX, num)
      res = self.readFaults(self.registers.LOGGED_FAULT_DETAIL)
      self.dumpReg('fault %d' % num, res)
      return res
