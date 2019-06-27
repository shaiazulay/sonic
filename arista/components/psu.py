from ..accessors.psu import MixedPsuImpl

from ..core.component import Component
from ..core.inventory import Psu

from ..drivers.pmbus import PmbusDriver

from .common import I2cComponent

class MixedPsuComponent(Component):
   def __init__(self, presenceComponent=None, statusComponent=None, **kwargs):
      self.presenceComponent=presenceComponent
      self.statusComponent=statusComponent
      super(MixedPsuComponent, self).__init__(**kwargs)

   def createPsu(self, psuId=1, led=None, presenceDriver=None, statusDriver=None):
      return MixedPsuImpl(psuId=psuId,
                  presenceDriver=self.presenceComponent.drivers[presenceDriver],
                  statusDriver=self.statusComponent.drivers[statusDriver], led=led)

class PmbusMixedPsuComponent(MixedPsuComponent):
   def createPsu(self, presenceDriver='PsuSysfsDriver', statusDriver='PmbusDriver',
                 **kwargs):
      return super(PmbusMixedPsuComponent, self).createPsu(
            presenceDriver=presenceDriver, statusDriver=statusDriver, **kwargs)

class UpperlakeMixedPsuComponent(MixedPsuComponent):
   def createPsu(self, presenceDriver='PsuSysfsDriver',
                 statusDriver='UpperlakePsuDriver', **kwargs):
      return super(UpperlakeMixedPsuComponent, self).createPsu(
            presenceDriver=presenceDriver, statusDriver=statusDriver, **kwargs)

class ScdPmbusPsu(Psu):
   def __init__(self, scd, pmbus):
      self.psuId = scd.psuId
      self.scd_ = scd
      self.pmbus_ = pmbus

   def getPresence(self):
      return self.scd_.getPresence()

   def getStatus(self):
      return self.pmbus_.getStatus()

class PmbusPsuComponent(I2cComponent):
   def __init__(self, addr, hwmonDir, drivers=None, **kwargs):
      sensors = ['curr1', 'curr2', 'curr3', 'in1', 'in2']
      if not drivers:
         drivers = [PmbusDriver(addr=addr, hwmonDir=hwmonDir, sensors=sensors)]
      super(PmbusPsuComponent, self).__init__(addr=addr, name="pmbus",
                                              waitFile=hwmonDir, drivers=drivers,
                                              **kwargs)
