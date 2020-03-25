from __future__ import absolute_import, division, print_function

from ...tests.testing import unittest

from ..diag import DiagContext
from ..register import RegisterMap, Register, RegBitField

class FakeRegisterMap(RegisterMap):
   REVISION = Register(0x01, name='revision')
   CONTROL = Register(0x02,
      RegBitField(0, 'writeOk', ro=False),
      RegBitField(1, 'failWrite'), # missing ro=False
      RegBitField(2, 'bit0'),
      RegBitField(3, 'bit1'),
   )
   STATUS = Register(0x03,
      RegBitField(0, 'shouldBeZero'),
      RegBitField(1, 'shouldBeOne'),
      RegBitField(2, 'invertZero', flip=True),
      RegBitField(3, 'invertOne', flip=True),
   )
   IOERROR = Register(0x04, name='ioError', ro=False)
   SCRATCHPAD = Register(0x05,
      RegBitField(3, 'bit3', ro=False),
      name='scratchpad', ro=False,
   )

class FakeDriver(object):
   def __init__(self):
      self.regmap = {
         0x01: 42,
         0x02: 0,
         0x03: 0b1010,
         0x04: 0, # should IOError
         0x05: 0,
      }

   def read(self, reg):
      if reg == 0x04:
         raise IOError(self, reg)
      return self.regmap[reg]

   def write(self, reg, value):
      if reg == 0x04:
         raise IOError(self, reg)
      self.regmap[reg] = value
      return value

class CoreRegisterTest(unittest.TestCase):
   def setUp(self):
      self.driver = FakeDriver()
      self.regs = FakeRegisterMap(self.driver)

   def testRevision(self):
      self.assertEqual(self.regs.revision(), 42)

   def testReadWrite(self):
      val = 1 << 3
      self.assertEqual(self.regs.scratchpad(), 0)

      self.regs.scratchpad(val)
      self.assertEqual(self.regs.scratchpad(), val)
      self.assertEqual(self.regs.bit3(), 1)

      self.regs.bit3(0)
      self.assertEqual(self.regs.bit3(), 0)
      self.assertEqual(self.regs.scratchpad(), 0)

      self.regs.scratchpad(0xff)
      self.assertEqual(self.regs.scratchpad(), 0xff)
      self.assertEqual(self.regs.bit3(), 1)

      self.regs.bit3(0)
      self.assertEqual(self.regs.scratchpad(), 0xf7)
      self.assertEqual(self.regs.bit3(), 0)
      self.regs.bit3(1)
      self.assertEqual(self.regs.scratchpad(), 0xff)
      self.assertEqual(self.regs.bit3(), 1)

   def testIoError(self):
      with self.assertRaises(IOError):
         self.regs.ioError()

      with self.assertRaises(IOError):
         self.regs.ioError(42)

   def testWriteSomething(self):
      self.regs.writeOk(1)
      with self.assertRaises(AssertionError):
         self.regs.failWrite(1)

   def testReadSomething(self):
      self.assertEqual(self.regs.shouldBeZero(), 0)
      self.assertEqual(self.regs.shouldBeOne(), 1)
      self.assertEqual(self.regs.invertZero(), 1)
      self.assertEqual(self.regs.invertOne(), 0)

   def testDiag(self):
      self.regs.__diag__(DiagContext())

if __name__ == '__main__':
   unittest.main()
