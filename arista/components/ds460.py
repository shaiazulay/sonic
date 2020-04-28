from .psu import PmbusPsu

from ..drivers.ds460 import Ds460I2cDriver

class Ds460(PmbusPsu):
   def __init__(self, addr=None, name='dps460', drivers=None, **kwargs):
      drivers = drivers or []
      drivers.extend([Ds460I2cDriver(name=name, addr=addr)])
      super(Ds460, self).__init__(addr=addr, name=name, drivers=drivers, **kwargs)
