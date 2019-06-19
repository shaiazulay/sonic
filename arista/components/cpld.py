import logging

from ..core.inventory import PowerCycle

from ..drivers.psu import UpperlakePsuDriver

from .common import I2cComponent

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
   def __init__(self, addr, drivers=None, **kwargs):
      self.powerCycles = []
      self.psus = []
      if not drivers:
         drivers = [UpperlakePsuDriver(addr=addr)]
      super(CrowCpld, self).__init__(addr=addr, drivers=drivers, **kwargs)

   def createPowerCycle(self, cmd=0x04, val=0xde):
      powerCycle = CpldPowerCycle(self.addr, cmd, val)
      self.powerCycles.append(powerCycle)
      return powerCycle

   def getPowerCycles(self):
      return self.powerCycles
