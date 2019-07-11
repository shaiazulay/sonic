from ..accessors.rook import RookLedImpl

from ..core.component import Component

from ..drivers.rook import RookLedSysfsDriver

class RookLedComponent(Component):
   def __init__(self, baseName=None, scd=None, drivers=None, **kwargs):
      self.baseName = baseName
      if not drivers:
         drivers = [RookLedSysfsDriver(sysfsPath='/sys/class/leds/')]
      super(RookLedComponent, self).__init__(drivers=drivers, **kwargs)

   def createLed(self, colors=None, name=None):
      return RookLedImpl(baseName=self.baseName, colors=colors or [], name=name,
                         driver=self.drivers['RookLedSysfsDriver'])
