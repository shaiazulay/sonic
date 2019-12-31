
from .i2c import I2cKernelDriver

class Max6658KernelDriver(I2cKernelDriver):
   def __init__(self, name='max6658', module='lm90', **kwargs):
      super(Max6658KernelDriver, self).__init__(name=name, module=module, **kwargs)
