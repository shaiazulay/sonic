from ..accessors.psu import MixedPsuImpl

from ..core.component import I2cComponent, Priority

from ..drivers.i2c import I2cKernelDriver
from ..drivers.pmbus import PmbusDriver
from ..drivers.sysfs import TempSysfsDriver

from .mixin import TempComponentMixin

class PmbusPsu(I2cComponent, TempComponentMixin):
   def __init__(self, addr=None, waitFile=None, name='pmbus', drivers=None,
                waitTimeout=25.0, priority=Priority.BACKGROUND, psus=None, **kwargs):
      gpios = ['curr1', 'curr2', 'curr3', 'in1', 'in2']
      drivers = drivers or []
      drivers.extend([I2cKernelDriver(name=name, addr=addr, waitFile=waitFile,
                                      waitTimeout=waitTimeout),
                      TempSysfsDriver(driverName='tempDriver', addr=addr),
                      PmbusDriver(driverName='psuStatusDriver', addr=addr,
                                  hwmonDir=waitFile, sensors=gpios)])
      super(PmbusPsu, self).__init__(addr=addr, waitFile=waitFile, name=name,
                                     drivers=drivers, waitTimeout=waitTimeout,
                                     priority=priority, psus=psus, **kwargs)
      psus = psus or []
      for psu in psus:
         self.createPsu(psuId=psu.psuId, led=psu.led, sensors=psu.sensors)

   def createPsu(self, psuId=1, led=None, sensors=None):
      self.addTempSensors(sensors)
      self.inventory.addPsu(MixedPsuImpl(psuId=psuId,
         presenceDriver=self.drivers['psuPresenceDriver'],
         statusDriver=self.drivers['psuStatusDriver'], led=led))

class UpperlakePsuComponent(I2cComponent, TempComponentMixin):
   def __init__(self, addr, waitFile=None, name='pmbus', drivers=None, cpld=None,
                waitTimeout=25.0, priority=Priority.BACKGROUND, psus=None, **kwargs):
      drivers = drivers or []
      drivers.extend([I2cKernelDriver(name=name, addr=addr, waitFile=waitFile,
                                      waitTimeout=waitTimeout),
                      TempSysfsDriver(driverName='tempDriver', addr=addr),
                      cpld.drivers['psuStatusDriver']])
      super(UpperlakePsuComponent, self).__init__(addr=addr, name=name,
                                                  drivers=drivers, waitFile=waitFile,
                                                  **kwargs)
      psus = psus or []
      for psu in psus:
         self.createPsu(psuId=psu.psuId, led=psu.led, sensors=psu.sensors)

   def createPsu(self, psuId=1, led=None, sensors=None):
      self.addTempSensors(sensors)
      self.inventory.addPsu(MixedPsuImpl(psuId=psuId,
         presenceDriver=self.drivers['psuPresenceDriver'],
         statusDriver=self.drivers['psuStatusDriver'], led=led))
