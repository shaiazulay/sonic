
from __future__ import absolute_import, division, print_function

import logging

from .i2c import I2cDevDriver

class SysCpldI2cDriver(I2cDevDriver):

   def __diag__(self, ctx):
      return {
         'regs': self.regs.__diag__(ctx),
      }
