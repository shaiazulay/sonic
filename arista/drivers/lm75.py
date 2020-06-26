
from .i2c import I2cKernelDriver

class Lm75KernelDriver(I2cKernelDriver):
   def __init__(self, name='lm75', module='lm75', **kwargs):
      super(Lm75KernelDriver, self).__init__(name=name, module=module, **kwargs)
