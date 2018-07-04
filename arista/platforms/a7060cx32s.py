from ..core.platform import registerPlatform, Platform
from ..core.driver import KernelDriver
from ..core.utils import incrange
from ..core.types import PciAddr, I2cAddr, NamedGpio, ResetGpio
from ..core.component import Priority
from ..core.inventory import Psu

from ..components.common import SwitchChip, I2cKernelComponent
from ..components.dpm import Ucd90120A
from ..components.cpld import CrowCpld
from ..components.scd import Scd

@registerPlatform(['DCS-7060CX-32S', 'DCS-7060CX-32S-ES'])
class Upperlake(Platform):
   class UpperlakePsu(Psu):
      def __init__(self, scd, psu):
         self.psuId = scd.psuId
         self.scd_ = scd
         self.psu_ = psu

      def getPresence(self):
         return self.scd_.getPresence()

      def getStatus(self):
         return self.psu_.getStatus()

   def __init__(self):
      super(Upperlake, self).__init__()

      self.sfpRange = incrange(33, 34)
      self.qsfp100gRange = incrange(1, 32)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.qsfp100gRange)

      self.addDriver(KernelDriver, 'crow-fan-driver')

      switchChip = SwitchChip(PciAddr(bus=0x01))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x02))
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      scd.addComponents([
         I2cKernelComponent(I2cAddr(2, 0x1a), 'max6697', '/sys/class/hwmon/hwmon1'),
         I2cKernelComponent(I2cAddr(3, 0x4c), 'max6658', '/sys/class/hwmon/hwmon2'),
         I2cKernelComponent(I2cAddr(3, 0x60), 'crow_cpld', '/sys/class/hwmon/hwmon3'),
         Ucd90120A(I2cAddr(3, 0x4e), priority=Priority.BACKGROUND),
         I2cKernelComponent(I2cAddr(5, 0x58), 'pmbus',
                            priority=Priority.BACKGROUND),
         I2cKernelComponent(I2cAddr(6, 0x58), 'pmbus',
                            priority=Priority.BACKGROUND),
         Ucd90120A(I2cAddr(7, 0x4e), priority=Priority.BACKGROUND),
      ])

      scd.addSmbusMasterRange(0x8000, 5, 0x80)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])
      self.inventory.addStatusLeds(['status', 'fan_status', 'psu1', 'psu2'])

      scd.addResets([
         ResetGpio(0x4000, 1, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 2, False, 'switch_chip_pcie_reset'),
      ])

      cpld = CrowCpld(I2cAddr(1, 0x23))
      self.inventory.addPowerCycle(cpld.createPowerCycle())
      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
      ])
      self.inventory.addPsus([
         self.UpperlakePsu(scd.createPsu(1),
                           cpld.createPsuComponent(1, priority=Priority.BACKGROUND)),
         self.UpperlakePsu(scd.createPsu(2),
                           cpld.createPsuComponent(2, priority=Priority.BACKGROUND)),
      ])
      scd.addComponents(cpld.getPsuComponents())

      addr = 0x6100
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLed(addr, name)
         self.inventory.addXcvrLed(xcvrId, name)
         addr += 0x10

      addr = 0x6140
      for xcvrId in self.qsfp100gRange:
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            scd.addLed(addr, name)
            self.inventory.addXcvrLed(xcvrId, name)
            addr += 0x10

      addr = 0x5010
      bus = 10
      for xcvrId in self.sfpRange:
         xcvr = scd.addSfp(addr, xcvrId, bus)
         self.inventory.addXcvr(xcvr)
         scd.addComponent(I2cKernelComponent(
            I2cAddr(bus, xcvr.eepromAddr), 'sff8436'))
         scd.addBusTweak(bus, xcvr.eepromAddr)
         addr += 0x10
         bus += 1

      addr = 0x5050
      bus = 18
      for xcvrId in self.qsfp100gRange:
         xcvr = scd.addQsfp(addr, xcvrId, bus)
         self.inventory.addXcvr(xcvr)
         scd.addComponent(I2cKernelComponent(
            I2cAddr(bus, xcvr.eepromAddr), 'sff8436'))
         scd.addBusTweak(bus, xcvr.eepromAddr)
         addr += 0x10
         bus += 1

