import logging

from contextlib import closing

from ..core.inventory import PowerCycle
from ..core.utils import SMBus

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

class SysCpld(I2cComponent):
   def __init__(self, addr, drivers=None, seuCfgReg=None, seuCfgBit=None,
                seuStsReg=None, seuStsBit=None,**kwargs):
      super(SysCpld, self).__init__(addr=addr, drivers=drivers, **kwargs)
      self.seuCfgReg = seuCfgReg
      self.seuCfgBit = seuCfgBit
      self.seuStsReg = seuStsReg
      self.seuStsBit = seuStsBit

   def readBit(self, reg, bit):
      with closing(SMBus(self.addr.bus)) as bus:
         reg = bus.read_byte_data(self.addr.address, reg)
         return (reg >> bit) & 0x1

   def writeBit(self, reg, bit, val):
      with closing(SMBus(self.addr.bus)) as bus:
         res = bus.read_byte_data(self.addr.address, reg)
         if (res >> bit) & 1 == val:
            return

         if val:
            res |= (1 << bit)
         else:
            res &= ~(1 << bit)

         bus.write_byte_data(self.addr.address, reg, res)

   def hasSeuError(self):
      return self.readBit(self.seuStsReg, self.seuStsBit)

   def powerCycleOnSeu(self, enable=None):
      with closing(SMBus(self.addr.bus)) as bus:
         if enable is None:
            return self.readBit(self.seuCfgReg, self.seuCfgBit) == 1
         else:
            return self.writeBit(self.seuCfgReg, self.seuCfgBit, int(enable))

class CrowCpld(SysCpld):
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
