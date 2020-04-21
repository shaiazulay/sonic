import time

from ..core.log import getLogger
from ..core.register import Register, RegisterMap

from ..drivers.cpld import SysCpldI2cDriver

from ..inventory.powercycle import PowerCycle

from .common import I2cComponent

logging = getLogger(__name__)

class SysCpldCommonRegisters(RegisterMap):
   REVISION = Register(0x01, name='revision')
   SCRATCHPAD = Register(0x02, name='scratchpad', ro=False)
   SUICIDE = Register(0x03, name='suicide', ro=False)
   POWER_CYCLE = Register(0x04, name='powerCycle', ro=False)

class SysCpldPowerCycle(PowerCycle):
   def __init__(self, parent):
      self.parent = parent

   def powerCycle(self):
      logging.info("Initiating powercycle through CPLD")
      self.parent.drivers['SysCpldI2cDriver'].regs.powerCycle(0xDE)
      logging.info("Powercycle triggered from CPLD")

class SysCpld(I2cComponent):
   def __init__(self, addr, drivers=None, registerCls=None, **kwargs):
      self.powerCycles = []
      if not drivers:
         drivers = [SysCpldI2cDriver(addr=addr, registerCls=registerCls)]
      super(SysCpld, self).__init__(addr=addr, drivers=drivers, **kwargs)

   def createPowerCycle(self):
      powerCycle = SysCpldPowerCycle(self)
      self.inventory.addPowerCycle(powerCycle)
      return powerCycle

   def getPowerCycles(self):
      return self.powerCycles

   def resetScd(self, sleep=1, wait=True):
      driver = self.drivers['SysCpldI2cDriver']
      state = driver.regs.scdReset()
      logging.debug('%s: scd reset: %s', self, state)

      driver.regs.scdReset(1)
      if wait:
         time.sleep(sleep) # could be lower
      driver.regs.scdReset(0)

   def powerCycleOnSeu(self, value=None):
      return self.drivers['SysCpldI2cDriver'].regs.powerCycleOnCrc(value)

   def hasSeuError(self):
      return self.drivers['SysCpldI2cDriver'].regs.scdCrcError()

