from ..accessors.psu import MixedPsuImpl

from ..core.component import Component, Priority

from ..drivers.i2c import I2cKernelDriver
from ..drivers.pmbus import PmbusDriver

from ..inventory.psu import Psu

from .common import I2cComponent

class MixedPsuComponent(Component):
   def __init__(self, presenceComponent=None, statusComponent=None, psus=None,
                **kwargs):
      self.presenceComponent=presenceComponent
      self.statusComponent=statusComponent
      super(MixedPsuComponent, self).__init__(**kwargs)
      psus = psus or []
      for psu in psus:
         self.createPsu(psuId=psu.psuId, led=psu.led)

   def createPsu(self, psuId=1, led=None, presenceDriver=None, statusDriver=None):
      psu = MixedPsuImpl(psuId=psuId,
                  presenceDriver=self.presenceComponent.drivers[presenceDriver],
                  statusDriver=self.statusComponent.drivers[statusDriver], led=led)
      self.inventory.addPsus([psu])

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

class PmbusPsu(I2cComponent):
   def __init__(self, addr, hwmonDir=None, name='pmbus', drivers=None,
                waitTimeout=25.0, priority=Priority.BACKGROUND, **kwargs):
      sensors = ['curr1', 'curr2', 'curr3', 'in1', 'in2']
      if not drivers:
         drivers = [I2cKernelDriver(name=name, addr=addr, waitFile=hwmonDir,
                                    waitTimeout=waitTimeout)]
         if hwmonDir is not None:
            drivers.append(PmbusDriver(addr=addr, hwmonDir=hwmonDir,
                                       sensors=sensors))
      super(PmbusPsu, self).__init__(addr=addr, name="pmbus", drivers=drivers,
                                     waitFile=hwmonDir, priority=priority, **kwargs)
