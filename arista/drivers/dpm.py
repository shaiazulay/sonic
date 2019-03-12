import logging

from ..core.driver import Driver
from ..core.i2c_utils import I2cMsg
from ..core.utils import inSimulation, SMBus

SMBUS_BLOCK_MAX_SZ = 32

class UcdI2cDevDriver(Driver):
   def __init__(self, registers=None, addr=None, **kwargs):
      super(UcdI2cDevDriver, self).__init__()
      self.bus = None
      self.busMsg = I2cMsg(addr)
      self.registers = registers
      self.addr = addr

   def __enter__(self):
      self.bus = SMBus(self.addr.bus)
      if not inSimulation():
         self.busMsg.open()
      return self

   def __exit__(self, *args):
      self.busMsg.close()
      self.bus.close()

   def dumpReg(self, name, data):
      logging.debug('%s reg: %s', name, ' '.join('%02x' % s for s in data))

   def getBlock(self, reg):
      size = self.bus.read_byte_data(self.addr.address, reg) + 1
      data = self.busMsg.getI2cBlock(self.addr.address, reg, size)
      return data[1:data[0]+1]

   def setBlock(self, reg, data):
      self.busMsg.setI2cBlock(self.addr.address, reg, [ len(data) ] + data)

   def getVersion(self):
      if inSimulation():
         return "SERIAL UCDSIM 2.3.4.0005 241218"
      data = self.getBlock(self.registers.MFR_SERIAL)
      serial = ''.join(chr(c) for c in data)
      data = self.getBlock(self.registers.DEVICE_ID)
      devid = ''.join(chr(c) for c in data if c).replace('|', ' ')
      return '%s %s' % (serial, devid)

   def readFaults(self):
      if inSimulation():
         return [ 0 ] * self.registers.LOGGED_FAULTS_COUNT
      res = self.getBlock(self.registers.LOGGED_FAULTS)
      self.dumpReg('faults', res)
      return res

   def clearFaults(self):
      if inSimulation():
         return
      reg = self.registers.LOGGED_FAULTS
      size = self.bus.read_byte_data(self.addr.address, reg)
      data = [ 0 ] * size
      self.setBlock(reg, data)

   def getFaultCount(self):
      if inSimulation():
         return 0
      reg = self.registers.LOGGED_FAULT_DETAIL_INDEX
      res = self.bus.read_word_data(self.addr.address, reg)
      return res >> 8

   def getFaultNum(self, num):
      if inSimulation():
         return [ 0 ] * self.registers.LOGGED_FAULT_DETAIL_COUNT
      self.bus.write_word_data(self.addr.address,
                               self.registers.LOGGED_FAULT_DETAIL_INDEX, num)
      res = self.getBlock(self.registers.LOGGED_FAULT_DETAIL)
      self.dumpReg('fault %d' % num, res)
      return res
