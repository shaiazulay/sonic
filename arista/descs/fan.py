
from __future__ import absolute_import, division, print_function

from ..core.desc import HwDesc

class FanDesc(HwDesc):
   def __init__(self, fanId, ledId=None, **kwargs):
      super(FanDesc, self).__init__(**kwargs)
      self.fanId = fanId
      self.ledId = ledId
