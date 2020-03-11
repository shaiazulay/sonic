from __future__ import absolute_import, division, print_function

from .i2c import I2cDevDriver
from ..core.register import Register
from ..core.utils import inSimulation

PCA9555_INPUT_REG = 0x0
PCA9555_OUTPUT_REG = 0x2
PCA9555_CONFIG_REG = 0x6

class GpioRegister(Register):
   '''Register's addr is more like offset in GpioRegister, which is 0x0 or 0x1.
   '''
   def readBit(self, bitpos):
      if inSimulation():
         return 0

      # Always read bits from input registers
      assert 0x0 <= self.addr <= 0x1
      regval = self.parent.read(PCA9555_INPUT_REG + self.addr)
      return (regval >> bitpos) & 1

   def writeBit(self, bitpos, value):
      if inSimulation():
         return

      # Read output registers, update bit, and write back
      # Doing the same for configuration registers,
      # in case they are modified unexpectedly.
      assert 0x0 <= self.addr <= 0x1
      def _writeBit(addr, value):
         regval = self.parent.read(addr)
         if value:
            regval |= (1 << bitpos)
         else:
            regval &= ~(1 << bitpos)
         self.parent.write(addr, regval)
      _writeBit(PCA9555_OUTPUT_REG + self.addr, value)
      _writeBit(PCA9555_CONFIG_REG + self.addr, False) # False for output

class Pca9555I2cDevDriver(I2cDevDriver):
   def reset(self):
      # Set all bits in config reg to have pins in input mode
      data = 0xff
      self.write(PCA9555_CONFIG_REG, data)
      self.write(PCA9555_CONFIG_REG + 1, data)

   def __diag__(self, ctx):
      return {
         'regs': self.regs.__diag__(ctx),
         'status': { reg : self.read(reg) for reg in range(8) },
      }
