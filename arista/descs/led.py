
from __future__ import absolute_import, division, print_function

from ..core.desc import HwDesc

class LedDesc(HwDesc):
   def __init__(self, name=None, colors=None, **kwargs):
      super(LedDesc, self).__init__(**kwargs)
      self.name = name
      self.colors = colors
