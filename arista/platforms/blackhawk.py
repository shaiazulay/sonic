from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.types import NamedGpio, PciAddr, ResetGpio
from ..core.utils import incrange

from ..components.asic.xgs.tomahawk3 import Tomahawk3
from ..components.cpu.rook import TehamaFanCpldComponent
from ..components.dpm import Ucd90320, UcdGpi
from ..components.max6581 import Max6581
from ..components.psu import PmbusPsu
from ..components.scd import Scd

from .cpu.rook import RookCpu

@registerPlatform()
class BlackhawkO(FixedSystem):

   SID = ['BlackhawkO']
   SKU = ['DCS-7060PX4-32']

   def __init__(self):
      super(BlackhawkO, self).__init__()

      self.osfpRange = incrange(1, 32)
      self.sfpRange = incrange(33, 34)

      self.inventory.addPorts(osfps=self.osfpRange, sfps=self.sfpRange)

      self.newComponent(Tomahawk3, PciAddr(bus=0x06))

      scd = self.newComponent(Scd, PciAddr(bus=0x07))
      self.scd = scd

      scd.createWatchdog()

      scd.newComponent(Max6581, scd.i2cAddr(8, 0x4d),
                       waitFile='/sys/class/hwmon/hwmon2')
      scd.newComponent(PmbusPsu, scd.i2cAddr(11, 0x58, t=3, datr=2, datw=3))
      scd.newComponent(PmbusPsu, scd.i2cAddr(12, 0x58, t=3, datr=2, datw=3))

      scd.addSmbusMasterRange(0x8000, 8, 0x80)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])

      scd.addResets([
         ResetGpio(0x4000, 4, False, 'sat_cpld1_reset'),
         ResetGpio(0x4000, 3, False, 'sat_cpld0_reset'),
         ResetGpio(0x4000, 2, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 0, False, 'security_asic_reset'),
      ])

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu2_present"),
         NamedGpio(0x5000, 1, True, False, "psu1_present"),
         NamedGpio(0x5000, 8, True, False, "psu2_status"),
         NamedGpio(0x5000, 9, True, False, "psu1_status"),
         NamedGpio(0x5000, 10, True, False, "psu2_ac_status"),
         NamedGpio(0x5000, 11, True, False, "psu1_ac_status"),
      ])

      scd.createPsu(1, led=self.inventory.getLed('psu1'))
      scd.createPsu(2, led=self.inventory.getLed('psu2'))

      addr = 0x6100
      for xcvrId in self.osfpRange:
         name = "osfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x40

      addr = 0x6900
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
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
         scd.addOsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

      addr = 0xA210
      bus = 48
      for xcvrId in sorted(self.sfpRange):
         scd.addSfp(addr, xcvrId, bus,
                    leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         addr += 0x10
         bus += 1

      cpu = self.newComponent(RookCpu, fanCount=5, mgmtBus=14,
                              fanCpldCls=TehamaFanCpldComponent)
      cpu.cpld.newComponent(Ucd90320, cpu.switchDpmAddr(0x11), causes={
         'overtemp': UcdGpi(1),
         'powerloss': UcdGpi(3),
         'watchdog': UcdGpi(5),
         'reboot': UcdGpi(7),
      })
      self.cpu = cpu
      self.syscpld = cpu.syscpld

@registerPlatform()
class BlackhawkDD(BlackhawkO):
   SID = ['BlackhawkDD']
   SKU = ['DCS-7060DX4-32']
