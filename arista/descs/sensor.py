
from __future__ import absolute_import, division, print_function

from ..core.desc import HwDesc

class Position(object):
   INLET = 'inlet'
   OUTLET = 'outlet'
   OTHER = 'other'

class SensorDesc(HwDesc):
   def __init__(self, diode, name, position, target, overheat, critical, **kwargs):
      super(SensorDesc, self).__init__(**kwargs)
      self.diode = diode
      self.name = name
      self.position = position
      self.target = target
      self.overheat = overheat
      self.critical = critical
