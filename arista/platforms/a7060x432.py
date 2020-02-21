from ..core.driver import KernelDriver
from ..core.platform import registerPlatform, Platform
from ..core.types import NamedGpio, PciAddr, ResetGpio
from ..core.utils import incrange

from ..components.common import SwitchChip
from ..components.cpu.rook import TehamaFanCpldComponent, RookSysCpld
from ..components.dpm import Ucd90320, UcdGpi
from ..components.max6581 import Max6581
from ..components.max6658 import Max6658
from ..components.psu import PmbusPsu
from ..components.scd import Scd

@registerPlatform()
class BlackhawkO(Platform):

   SID = ['BlackhawkO']
   SKU = ['DCS-7060PX4-32']

   def __init__(self):
      super(BlackhawkO, self).__init__()

      self.osfpRange = incrange(1, 32)
      self.sfpRange = incrange(33, 34)

      self.inventory.addPorts(osfps=self.osfpRange, sfps=self.sfpRange)

      self.addDriver(KernelDriver, 'rook-led-driver')

      switchChip = SwitchChip(PciAddr(bus=0x06))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x07))
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      scd.addComponents([
         Max6581(scd.i2cAddr(8, 0x4d), waitFile='/sys/class/hwmon/hwmon2'),
         PmbusPsu(scd.i2cAddr(11, 0x58, t=3, datr=2, datw=3)),
         PmbusPsu(scd.i2cAddr(12, 0x58, t=3, datr=2, datw=3)),
      ])

      scd.addSmbusMasterRange(0x8000, 8, 0x80)

      self.inventory.addLeds(scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ]))

      self.inventory.addResets(scd.addResets([
         ResetGpio(0x4000, 4, False, 'sat_cpld1_reset'),
         ResetGpio(0x4000, 3, False, 'sat_cpld0_reset'),
         ResetGpio(0x4000, 2, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 0, False, 'security_asic_reset'),
      ]))

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu2_present"),
         NamedGpio(0x5000, 1, True, False, "psu1_present"),
         NamedGpio(0x5000, 8, True, False, "psu2_status"),
         NamedGpio(0x5000, 9, True, False, "psu1_status"),
         NamedGpio(0x5000, 10, True, False, "psu2_ac_status"),
         NamedGpio(0x5000, 11, True, False, "psu1_ac_status"),
      ])

      self.inventory.addPsus([
         scd.createPsu(1, led=self.inventory.getLed('psu1')),
         scd.createPsu(2, led=self.inventory.getLed('psu2')),
      ])

      addr = 0x6100
      for xcvrId in self.osfpRange:
         name = "osfp%d" % xcvrId
         self.inventory.addLedGroup(name, [scd.addLed(addr, name)])
         addr += 0x40

      addr = 0x6900
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         self.inventory.addLedGroup(name, [scd.addLed(addr, name)])
         addr += 0x40

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xA010
      bus = 16
      for xcvrId in sorted(self.osfpRange):
         intr = intrRegs[1].getInterruptBit(xcvrId - 1)
         name = 'osfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         xcvr = scd.addOsfp(addr, xcvrId, bus, interruptLine=intr,
                            leds=self.inventory.getLedGroup(name))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

      addr = 0xA210
      bus = 48
      for xcvrId in sorted(self.sfpRange):
         xcvr = scd.addSfp(addr, xcvrId, bus,
                           leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

      cpld = Scd(PciAddr(bus=0xff, device=0x0b, func=3))
      self.addComponent(cpld)

      tehamaFanCpldAddr = cpld.i2cAddr(12, 0x60)
      tehamaFanComponent = TehamaFanCpldComponent(addr=tehamaFanCpldAddr,
                                                  waitFile='/sys/class/hwmon/hwmon4')

      for fanId in incrange(1, 5):
         self.inventory.addFan(tehamaFanComponent.createFan(fanId))

      cpld.addSmbusMasterRange(0x8000, 4, 0x80, 4)
      cpld.addComponents([
         Max6658(cpld.i2cAddr(0, 0x4c), waitFile='/sys/class/hwmon/hwmon3'),
         Ucd90320(cpld.i2cAddr(10, 0x11, t=3), causes={
            'overtemp': UcdGpi(1),
            'powerloss': UcdGpi(3),
            'watchdog': UcdGpi(5),
            'reboot': UcdGpi(7),
         }),
         tehamaFanComponent,
      ])

      self.inventory.addPowerCycle(cpld.createPowerCycle())

      self.syscpld = RookSysCpld(cpld.i2cAddr(8, 0x23))
      self.addComponent(self.syscpld)

@registerPlatform()
class BlackhawkDD(BlackhawkO):
   SID = ['BlackhawkDD']
   SKU = ['DCS-7060DX4-32']
