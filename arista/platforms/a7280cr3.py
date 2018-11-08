from ..core.platform import registerPlatform, Platform
from ..core.utils import incrange
from ..core.types import PciAddr, NamedGpio, ResetGpio
from ..core.component import Priority

from ..components.common import SwitchChip, I2cKernelComponent
from ..components.dpm import Ucd90160, Ucd90320, UcdGpi
from ..components.scd import Scd
from ..components.phy import Babbage

@registerPlatform(['DCS-7280CR3-32P4'])
class Smartsville(Platform):
   def __init__(self):
      super(Smartsville, self).__init__()

      self.qsfpRange = incrange(1, 32)
      self.osfpRange = incrange(33, 36)

      self.inventory.addPorts(qsfps=self.qsfpRange, osfps=self.osfpRange)

      switchChip = SwitchChip(PciAddr(bus=0x05))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x02))
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      scd.addComponents([
         I2cKernelComponent(scd.i2cAddr(0, 0x48), 'tmp468',
                            '/sys/class/hwmon/hwmon2'),
         I2cKernelComponent(scd.i2cAddr(6, 0x58), 'pmbus',
                            priority=Priority.BACKGROUND),
         I2cKernelComponent(scd.i2cAddr(7, 0x58), 'pmbus',
                            priority=Priority.BACKGROUND),
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

      self.inventory.addResets(scd.addResets([
         ResetGpio(0x4000, 0, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 1, False, 'switch_chip_pcie_reset'),
         ResetGpio(0x4000, 2, False, 'security_asic_reset'),
      ]))

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
         NamedGpio(0x5000, 8, True, False, "psu1_status"),
         NamedGpio(0x5000, 9, True, False, "psu2_status"),
         NamedGpio(0x5000, 10, True, False, "psu1_ac_status"),
         NamedGpio(0x5000, 11, True, False, "psu2_ac_status"),

         NamedGpio(0x5000, 16, False, False, "psu1_present_changed"),
         NamedGpio(0x5000, 17, False, False, "psu2_present_changed"),
         NamedGpio(0x5000, 18, False, False, "psu1_status_changed"),
         NamedGpio(0x5000, 19, False, False, "psu2_status_changed"),
         NamedGpio(0x5000, 20, False, False, "psu1_ac_status_changed"),
         NamedGpio(0x5000, 21, False, False, "psu2_ac_status_changed"),
      ])
      self.inventory.addPsus([
         scd.createPsu(1),
         scd.createPsu(2),
      ])

      addr = 0x6100
      for xcvrId in self.qsfpRange:
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            scd.addLed(addr, name)
            self.inventory.addXcvrLed(xcvrId, name)
            addr += 0x40
      for xcvrId in self.osfpRange:
         for laneId in incrange(1, 4):
            name = "osfp%d_%d" % (xcvrId, laneId)
            scd.addLed(addr, name)
            self.inventory.addXcvrLed(xcvrId, name)
            addr += 0x40

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xA010
      bus = 8
      for xcvrId in self.qsfpRange:
         intr = intrRegs[1].getInterruptBit(xcvrId - self.qsfpRange[0])
         self.inventory.addInterrupt('qsfp%d' % xcvrId, intr)
         xcvr = scd.addQsfp(addr, xcvrId, bus, interruptLine=intr)
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1
      for xcvrId in self.osfpRange:
         intr = intrRegs[2].getInterruptBit(xcvrId - self.osfpRange[0])
         self.inventory.addInterrupt('osfp%d' % xcvrId, intr)
         xcvr = scd.addOsfp(addr, xcvrId, bus, interruptLine=intr)
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

      scd.addMdioMasterRange(0x9000, 8)

      for i in range( 0, 8 ):
         phyId = i + 1
         reset = scd.addReset( ResetGpio( 0x4000, 3 + i, False, 'phy%d_reset' %
                               phyId ) )
         self.inventory.addReset( reset )
         phy = Babbage( phyId, reset=reset, mdio=scd.addMdio( i, 0 ) )
         self.inventory.addPhy( phy )

      cpld = Scd(PciAddr(bus=0x00, device=0x09, func=0))
      self.addComponent(cpld)

      cpld.addSmbusMasterRange(0x8000, 2, 0x80, 4)
      cpld.addComponents([
         I2cKernelComponent(cpld.i2cAddr(0, 0x4c), 'max6658'),
         Ucd90160(cpld.i2cAddr(1, 0x4e), priority=Priority.BACKGROUND),
         Ucd90320(cpld.i2cAddr(5, 0x11), priority=Priority.BACKGROUND, causes={
            'powerloss': UcdGpi(1),
            'reboot': UcdGpi(2),
            'watchdog': UcdGpi(3),
            'overtemp': UcdGpi(4),
         }),
      ])
      self.inventory.addPowerCycle(cpld.createPowerCycle())
