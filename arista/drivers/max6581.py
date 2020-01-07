
from .i2c import I2cKernelDriver

class Max6581KernelDriver(I2cKernelDriver):
   def __init__(self, name='max6581', module='max6697', **kwargs):
      super(Max6581KernelDriver, self).__init__(name=name, module=module, **kwargs)

