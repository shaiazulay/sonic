from .common import I2cComponent

from ..core.component import Priority

from ..drivers.ds460 import Ds460I2cDriver
from ..drivers.i2c import I2cKernelDriver
from ..drivers.pmbus import PmbusDriver

class Ds460(I2cComponent):
   def __init__(self, addr, hwmonDir, name='dps460', drivers=None,
                priority=Priority.BACKGROUND, waitTimeout=30.0, **kwargs):
      self.name = name
      sensors = ['curr1', 'curr2', 'curr3', 'in1', 'in2']
      if not drivers:
         drivers = [Ds460I2cDriver(name=name, addr=addr),
                    I2cKernelDriver(name=name, addr=addr, waitFile=hwmonDir,
                                    waitTimeout=waitTimeout),
                    PmbusDriver(addr=addr, hwmonDir=hwmonDir, sensors=sensors)]
      super(Ds460, self).__init__(addr=addr, name=name, drivers=drivers,
                                  priority=priority, **kwargs)
