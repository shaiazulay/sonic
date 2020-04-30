
from __future__ import absolute_import, division, print_function

from ..core.desc import HwDesc

class PsuDesc(HwDesc):
   def __init__(self, psuId, led=None, sensors=None, **kwargs):
      super(PsuDesc, self).__init__(**kwargs)
      self.psuId = psuId
      self.led = led
      self.sensors = sensors or []
