
from .i2c import I2cKernelDriver

class Lm73KernelDriver(I2cKernelDriver):
   def __init__(self, name='lm73', module='lm73', **kwargs):
      super(Lm73KernelDriver, self).__init__(name=name, module=module, **kwargs)
