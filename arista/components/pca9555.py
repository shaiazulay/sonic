from __future__ import absolute_import, division, print_function

from .common import I2cComponent

from ..drivers.pca9555 import Pca9555I2cDevDriver

class Pca9555(I2cComponent):
   def __init__(self, addr, drivers=None, registerCls=None, **kwargs):
      if not drivers:
         drivers = [Pca9555I2cDevDriver(addr=addr, registerCls=registerCls)]
      super(Pca9555, self).__init__(addr=addr, drivers=drivers, **kwargs)

   def resetConfig(self):
      self.drivers['Pca9555I2cDevDriver'].reset()

   def __getattr__(self, key):
      driver = self.drivers['Pca9555I2cDevDriver']
      return getattr(driver.regs, key)
