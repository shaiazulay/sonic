
from __future__ import absolute_import, division, print_function

from ..core.desc import HwDesc

class GpioDesc(HwDesc):
   def __init__(self, name, addr, bit, ro=False, activeLow=False, **kwargs):
      super(GpioDesc, self).__init__(**kwargs)

      self.name = name
      self.addr = addr
      self.bit = bit
      self.ro = ro
      self.activeLow = activeLow
