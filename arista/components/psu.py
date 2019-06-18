import logging

from contextlib import closing

from ..core.inventory import Psu
from ..core.component import Component
from ..core.utils import SMBus
from ..drivers.accessors import MixedPsuImpl
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

   def getStatus(self):
      return self.drivers['PmbusDriver'].getStatus()

class UpperlakePsuComponent(I2cComponent):
   def __init__(self, psuId=1, **kwargs):
      # MSB: Description (Good/bad values)
      # 3:   PSU1 AC OK (1/0)
      # 2:   PSU2 AC OK (1/0)
      # 1:   PSU1 DC OK (1/0)
      # 0:   PSU2 DC OK (1/0)
      self.statusMask_ = 0b1010 >> (psuId - 1)
      super(UpperlakePsuComponent, self).__init__(**kwargs)

   def getStatus(self):
      reg = 0x0c
      logging.debug('i2c-read %d %#02x %#02x', self.addr.bus, self.addr.address, reg)

      # Both AC and DC status bits must be on.
      with closing(SMBus(self.addr.bus)) as bus:
         state = bus.read_byte_data(self.addr.address, reg)
         logging.debug('psu state is %#02x', state)
         return state & self.statusMask_ == self.statusMask_
