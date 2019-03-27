import logging

from ..core.inventory import PowerCycle

from .common import I2cComponent
from .psu import UpperlakePsuComponent

class CpldPowerCycle(PowerCycle):
   def __init__(self, addr, cmd, val):
      self.addr = addr
      self.cmd = cmd
      self.val = val

   def powerCycle(self):
      import smbus
      bus = smbus.SMBus(self.addr.bus)
      logging.info("Initiating powercycle through CPLD")
      bus.write_byte_data(self.addr.address, self.cmd, self.val)
      logging.info("Powercycle triggered from CPLD")

class CrowCpld(I2cComponent):
   def __init__(self, addr, **kwargs):
      self.addr = addr
      self.powerCycles = []
      self.psus = []
      super(CrowCpld, self).__init__(**kwargs)

   def createPsuComponent(self, num, **kwargs):
      psuComponent = UpperlakePsuComponent(psuId=num, addr=self.addr, **kwargs)
      self.psus.append(psuComponent)
      return psuComponent

   def getPsuComponents(self):
      return self.psus

   def createPowerCycle(self, cmd=0x04, val=0xde):
      powerCycle = CpldPowerCycle(self.addr, cmd, val)
      self.powerCycles.append(powerCycle)
      return powerCycle

   def getPowerCycles(self):
      return self.powerCycles
