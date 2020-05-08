# For backward compatibility - there are a bunch of things
# which import the following things from arista.components.common,
# but they are actually moved to other places.
from ..core.component import PciComponent, I2cComponent
from ..core.asic import SwitchChip

from ..drivers.i2c import I2cKernelDriver

# Do not use this class as it is being depreciated
class I2cKernelComponent(I2cComponent):
   def __init__(self, addr, name, waitFile=None, waitTimeout=None, **kwargs):
      drivers = [I2cKernelDriver(name=name, addr=addr, waitFile=waitFile,
                                 waitTimeout=waitTimeout)]
      super(I2cKernelComponent, self).__init__(addr=addr, name=name,
                                               drivers=drivers, **kwargs)
