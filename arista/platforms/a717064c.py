from ..core.platform import registerPlatform, Platform
from ..core.driver import KernelDriver
from ..core.utils import incrange
from ..core.types import PciAddr, I2cAddr, NamedGpio, ResetGpio
from ..core.component import Priority

from ..components.common import SwitchChip, I2cKernelComponent
from ..components.dpm import Ucd90120A, Ucd90160
from ..components.scd import Scd

@registerPlatform(['DCS-7170-64', 'DCS-7170-64C', 'DCS-7170-64C-SSD'])
class Alhambra(Platform):
   def __init__(self):
      super(Alhambra, self).__init__()

      self.qsfpRange = incrange(1, 64)
      self.sfpRange = incrange(65, 66)

      self.inventory.addPorts(qsfps=self.qsfpRange, sfps=self.sfpRange)

      self.addDriver(KernelDriver, 'rook-fan-cpld')
      self.addDriver(KernelDriver, 'rook-led-driver')

      switchChip = SwitchChip(PciAddr(bus=0x07))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x06), newDriver=True)
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      scd.addComponents([
         I2cKernelComponent(I2cAddr(8, 0x4c), 'max6658'),
         I2cKernelComponent(I2cAddr(6, 0x58), 'dps1900',
                            priority=Priority.BACKGROUND),
         I2cKernelComponent(I2cAddr(7, 0x58), 'dps1900',
                            priority=Priority.BACKGROUND),
      ])

      scd.addSmbusMasterRange(0x8000, 9, 0x80)

      self.inventory.addResets(scd.addResets([
         ResetGpio(0x4000, 8, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 1, False, 'security_chip_reset'),
         ResetGpio(0x4000, 0, False, 'repeater_sfp_reset'),
      ]))

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
         NamedGpio(0x5000, 8, True, False, "psu1_status"),
         NamedGpio(0x5000, 9, True, False, "psu2_status"),
         NamedGpio(0x5000, 10, True, False, "psu1_ac_status"),
         NamedGpio(0x5000, 11, True, False, "psu2_ac_status"),
      ])
      self.inventory.addPsus([scd.createPsu(1), scd.createPsu(2)])

      addr = 0x6100
      for xcvrId in self.qsfpRange:
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            scd.addLed(addr, name)
            self.inventory.addXcvrLed(xcvrId, name)
            addr += 0x10

      addr = 0x7200
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLed(addr, name)
         self.inventory.addXcvrLed(xcvrId, name)
         addr += 0x10

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xA010
      bus = 9
      for xcvrId in sorted(self.qsfpRange):
         intr = intrRegs[xcvrId // 33 + 1].getInterruptBit((xcvrId - 1) % 32)
         self.inventory.addInterrupt('qsfp%d' % xcvrId, intr)
         xcvr = scd.addQsfp(addr, xcvrId, bus, interruptLine=intr)
         self.inventory.addXcvr(xcvr)
         scd.addComponent(I2cKernelComponent(
            I2cAddr(bus, xcvr.eepromAddr), 'sff8436'))
         addr += 0x10
         bus += 1

      addr = 0xA500
      bus = 73
      for xcvrId in sorted(self.sfpRange):
         xcvr = scd.addSfp(addr, xcvrId, bus)
         self.inventory.addXcvr(xcvr)
         scd.addComponent(I2cKernelComponent(
            I2cAddr(bus, xcvr.eepromAddr), 'sff8436'))
         addr += 0x10
         bus += 1

      cpld = Scd(PciAddr(bus=0xff, device=0x0b, func=3), newDriver=True)
      self.addComponent(cpld)

      cpld.addSmbusMasterRange(0x8000, 4, 0x80, 4)
      cpld.addComponents([
         I2cKernelComponent(I2cAddr(81, 0x4c), 'max6658'),
         Ucd90160(I2cAddr(82, 0x4e), priority=Priority.BACKGROUND),
         Ucd90120A(I2cAddr(91, 0x4e), priority=Priority.BACKGROUND),
         I2cKernelComponent(I2cAddr(93, 0x60), 'rook_cpld'),
         I2cKernelComponent(I2cAddr(96, 0x20), 'rook_leds'),
         I2cKernelComponent(I2cAddr(96, 0x48), 'lm73'),
      ])
