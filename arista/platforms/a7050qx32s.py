from ..core.platform import registerPlatform, Platform
from ..core.driver import KernelDriver
from ..core.utils import incrange
from ..core.types import PciAddr, I2cAddr, NamedGpio, ResetGpio
from ..core.component import Priority

from ..components.common import SwitchChip, I2cKernelComponent
from ..components.psu import PmbusPsuComponent, ScdPmbusPsu
from ..components.scd import Scd
from ..components.ds125br import Ds125Br

@registerPlatform('DCS-7050QX-32S')
class Clearlake(Platform):
   def __init__(self):
      super(Clearlake, self).__init__()

      self.sfpRange = incrange(1, 4)
      self.qsfp40gAutoRange = incrange(5, 28)
      self.qsfp40gOnlyRange = incrange(29, 36)
      self.allQsfps = sorted(self.qsfp40gAutoRange + self.qsfp40gOnlyRange)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.allQsfps)

      self.addDriver(KernelDriver, 'crow-fan-driver', '/sys/class/hwmon/hwmon1')

      switchChip = SwitchChip(PciAddr(bus=0x01))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x02))
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      self.inventory.addPowerCycle(scd.createPowerCycle())

      scd.addComponents([
         I2cKernelComponent(I2cAddr(2, 0x4c), 'max6658', '/sys/class/hwmon/hwmon2'),
         I2cKernelComponent(I2cAddr(3, 0x4c), 'max6658', '/sys/class/hwmon/hwmon3'),
         I2cKernelComponent(I2cAddr(3, 0x60), 'crow_cpld', '/sys/class/hwmon/hwmon4'),
         # Handling of the DPM is disabled because this functionality is unstable.
         #I2cKernelComponent(I2cAddr(3, 0x4e), 'pmbus',
         #                   priority=Priority.BACKGROUND), # ucd90120A
         I2cKernelComponent(I2cAddr(5, 0x58), 'pmbus',
                            priority=Priority.BACKGROUND),
         I2cKernelComponent(I2cAddr(6, 0x58), 'pmbus',
                            priority=Priority.BACKGROUND),
         # Handling of the DPM is disabled because this functionality is unstable.
         #I2cKernelComponent(I2cAddr(7, 0x4e), 'pmbus',
         #                   priority=Priority.BACKGROUND), # ucd90120A
         Ds125Br(I2cAddr(8, 0xff)),
      ])

      scd.addSmbusMasterRange(0x8000, 6)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])
      self.inventory.addStatusLeds(['status', 'fan_status', 'psu1',
         'psu2'])

      scd.addReset(ResetGpio(0x4000, 0, False, 'switch_chip_reset'))

      psu1 = PmbusPsuComponent(I2cAddr(5, 0x58), '/sys/class/hwmon/hwmon5',
                               priority=Priority.BACKGROUND)
      psu2 = PmbusPsuComponent(I2cAddr(6, 0x58), '/sys/class/hwmon/hwmon6',
                               priority=Priority.BACKGROUND)
      scd.addComponents([psu1, psu2])
      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
         NamedGpio(0x6940, 0, False, False, "mux"), # FIXME: oldSetup order/name
      ])
      self.inventory.addPsus([
         ScdPmbusPsu(scd.createPsu(1, statusGpios=None), psu1),
         ScdPmbusPsu(scd.createPsu(2, statusGpios=None), psu2),
      ])

      addr = 0x6100
      for xcvrId in self.qsfp40gAutoRange:
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            scd.addLed(addr, name)
            self.inventory.addXcvrLed(xcvrId, name)
            addr += 0x10

      addr = 0x6720
      for xcvrId in self.qsfp40gOnlyRange:
         name = "qsfp%d" % xcvrId
         scd.addLed(addr, name)
         self.inventory.addXcvrLed(xcvrId, name)
         addr += 0x30 if xcvrId % 2 else 0x50

      addr = 0x6900
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLed(addr, name)
         self.inventory.addXcvrLed(xcvrId, name)
         addr += 0x10

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
      ]

      addr = 0x5010
      bus = 10
      for xcvrId in self.allQsfps:
         intr = intrRegs[1].getInterruptBit(xcvrId - 5)
         self.inventory.addInterrupt('qsfp%d' % xcvrId, intr)
         xcvr = scd.addQsfp(addr, xcvrId, bus, interruptLine=intr)
         self.inventory.addXcvr(xcvr)
         scd.addComponent(I2cKernelComponent(
            I2cAddr(bus, xcvr.eepromAddr), 'sff8436'))
         scd.addBusTweak(bus, xcvr.eepromAddr)
         addr += 0x10
         bus += 1

      addr = 0x5210
      bus = 42
      for xcvrId in sorted(self.sfpRange):
         xcvr = scd.addSfp(addr, xcvrId, bus)
         self.inventory.addXcvr(xcvr)
         scd.addComponent(I2cKernelComponent(
            I2cAddr(bus, xcvr.eepromAddr), 'sff8436'))
         scd.addBusTweak(bus, xcvr.eepromAddr)
         addr += 0x10
         bus += 1

@registerPlatform('DCS-7050QX2-32S')
class ClearlakePlus(Clearlake):
   pass

