from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.types import PciAddr, NamedGpio, ResetGpio
from ..core.utils import incrange

from ..components.common import SwitchChip
from ..components.dpm import Ucd90160, Ucd90320, UcdGpi
from ..components.phy.babbage import Babbage
from ..components.psu import PmbusPsu
from ..components.scd import Scd
from ..components.tmp468 import Tmp468

from .cpu.woodpecker import WoodpeckerCpu

@registerPlatform()
class Smartsville(FixedSystem):

   SID = ['Smartsville', 'SmartsvilleSsd']
   SKU = ['DCS-7280CR3-32P4', 'DCS-7280CR3-32P4-M']

   def __init__(self):
      super(Smartsville, self).__init__()

      self.cpu = self.newComponent(WoodpeckerCpu)
      self.cpu.cpld.newComponent(Ucd90160, self.cpu.cpuDpmAddr())
      self.cpu.cpld.newComponent(Ucd90320, self.cpu.switchDpmAddr(),  causes={
         'powerloss': UcdGpi(1),
         'reboot': UcdGpi(2),
         'watchdog': UcdGpi(3),
         'overtemp': UcdGpi(4),
      })

      self.qsfpRange = incrange(1, 32)
      self.osfpRange = incrange(33, 36)

      self.inventory.addPorts(qsfps=self.qsfpRange, osfps=self.osfpRange)

      self.newComponent(SwitchChip, PciAddr(bus=0x05))

      scd = self.newComponent(Scd, PciAddr(bus=0x02))

      scd.createWatchdog()

      scd.newComponent(Tmp468, scd.i2cAddr(0, 0x48),
                       waitFile='/sys/class/hwmon/hwmon4')
      scd.newComponent(PmbusPsu, scd.i2cAddr(6, 0x58, t=3, datr=3, datw=3))
      scd.newComponent(PmbusPsu, scd.i2cAddr(7, 0x58, t=3, datr=3, datw=3))

      scd.addSmbusMasterRange(0x8000, 5, 0x80)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])

      scd.addResets([
         ResetGpio(0x4000, 0, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 1, False, 'switch_chip_pcie_reset'),
         ResetGpio(0x4000, 2, False, 'security_asic_reset'),
      ])

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
      scd.createPsu(1, led=self.inventory.getLed('psu1'))
      scd.createPsu(2, led=self.inventory.getLed('psu2'))

      addr = 0x6100
      for xcvrId in self.qsfpRange:
         leds = []
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            leds.append((addr, name))
            addr += 0x10
         scd.addLedGroup("qsfp%d" % xcvrId, leds)

      addr = 0x6900
      for xcvrId in self.osfpRange:
         name = "osfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x40

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xA010
      bus = 8
      for index, xcvrId in enumerate(self.qsfpRange):
         intr = intrRegs[1].getInterruptBit(index)
         name = 'qsfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1
      for index, xcvrId in enumerate(self.osfpRange):
         intr = intrRegs[2].getInterruptBit(index)
         name = 'osfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         scd.addOsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

      scd.addMdioMasterRange(0x9000, 8)

      for i in range(0, 8):
         phyId = i + 1
         reset = scd.addReset(ResetGpio(0x4000, 3 + i, False,
                                        'phy%d_reset' % phyId))
         mdios = [scd.addMdio(i, 0), scd.addMdio(i, 1)]
         phy = Babbage(phyId, mdios, reset=reset)
         self.inventory.addPhy(phy)

@registerPlatform()
class SmartsvilleBK(Smartsville):
   SID = ['SmartsvilleBK']
   SKU = ['DCS-7280CR3K-32P4']

@registerPlatform()
class SmartsvilleDD(Smartsville):
   SID = ['SmartsvilleDD', 'SmartsvilleDDSsd']
   SKU = ['DCS-7280CR3-32D4', 'DCS-7280CR3-32D4-M']

@registerPlatform()
class SmartsvilleDDBK(Smartsville):
   SID = ['SmartsvilleDDBK']
   SKU = ['DCS-7280CR3K-32D4']

@registerPlatform()
class SmartsvilleBkMs(Smartsville):
   SID = ['SmartsvilleBkMs']
   SKU = ['DCS-7280CR3MK-32P4']
