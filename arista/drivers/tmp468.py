
from .i2c import I2cKernelDriver

class Tmp468KernelDriver(I2cKernelDriver):
   def __init__(self, name='tmp468', module='tmp468', **kwargs):
      super(Tmp468KernelDriver, self).__init__(name=name, module=module, **kwargs)
