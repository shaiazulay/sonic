from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.types import PciAddr, ResetGpio
from ..core.utils import incrange

from ..components.common import SwitchChip
from ..components.cpu.amd.k10temp import K10Temp
from ..components.dpm import Ucd90160, Ucd90320, UcdGpi
from ..components.phy.babbage import Babbage
from ..components.psu import PmbusPsu
from ..components.scd import Scd
from ..components.tmp468 import Tmp468

from .cpu.woodpecker import WoodpeckerCpu

from ..descs.gpio import GpioDesc
from ..descs.psu import PsuDesc
from ..descs.sensor import Position, SensorDesc

@registerPlatform()
class Smartsville(FixedSystem):

   SID = ['Smartsville', 'SmartsvilleSsd']
   SKU = ['DCS-7280CR3-32P4', 'DCS-7280CR3-32P4-M']

   def __init__(self):
      super(Smartsville, self).__init__()

      self.cpu = self.newComponent(WoodpeckerCpu)
      self.cpu.cpld.newComponent(Ucd90160, self.cpu.cpuDpmAddr())
      self.cpu.cpld.newComponent(Ucd90320, self.cpu.switchDpmAddr(), causes={
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

      self.newComponent(K10Temp, waitFile='/sys/class/hwmon/hwmon1', sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=70, overheat=95, critical=115),
      ])

      scd.newComponent(Tmp468, scd.i2cAddr(0, 0x48),
                       waitFile='/sys/class/hwmon/hwmon4', sensors=[
         SensorDesc(diode=0, name='Board Sensor',
                    position=Position.OTHER, target=65, overheat=75, critical=80),
         SensorDesc(diode=1, name='Front Air',
                    position=Position.INLET, target=55, overheat=65, critical=75),
         SensorDesc(diode=2, name='Rear Air',
                    position=Position.OTHER, target=55, overheat=65, critical=75),
         SensorDesc(diode=7, name='Fap 0 Core 0',
                    position=Position.OTHER, target=85, overheat=100, critical=110),
         SensorDesc(diode=8, name='Fap 0 Core 1',
                    position=Position.OTHER, target=85, overheat=100, critical=110),
      ])

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
         GpioDesc("psu1_present", 0x5000, 0, ro=True),
         GpioDesc("psu2_present", 0x5000, 1, ro=True),
         GpioDesc("psu1_status", 0x5000, 8, ro=True),
         GpioDesc("psu2_status", 0x5000, 9, ro=True),
         GpioDesc("psu1_ac_status", 0x5000, 10, ro=True),
         GpioDesc("psu2_ac_status", 0x5000, 11, ro=True),

         GpioDesc("psu1_present_changed", 0x5000, 16),
         GpioDesc("psu2_present_changed", 0x5000, 17),
         GpioDesc("psu1_status_changed", 0x5000, 18),
         GpioDesc("psu2_status_changed", 0x5000, 19),
         GpioDesc("psu1_ac_status_changed", 0x5000, 20),
         GpioDesc("psu2_ac_status_changed", 0x5000, 21),
      ])

      for psuId in incrange(1, 2):
         scd.addPsu(PmbusPsu,
                    addr=scd.i2cAddr(5 + psuId, 0x58, t=3, datr=3, datw=3),
                    waitFile="/sys/class/hwmon/hwmon%d" % (4 + psuId),
                    psus=[
            PsuDesc(psuId=psuId,
                    led=scd.inventory.getLed('psu%d' % psuId), sensors=[
               SensorDesc(diode=0,
                          name='Power supply %d inlet temp sensor' % psuId,
                          position=Position.INLET,
                          target=60, overheat=75, critical=85),
               SensorDesc(diode=1,
                          name='Power supply %d secondary hotspot sensor' % psuId,
                          position=Position.OTHER,
                          target=70, overheat=105, critical=110),
               SensorDesc(diode=2,
                          name='Power supply %d primary hotspot sensor' % psuId,
                          position=Position.OTHER,
                          target=70, overheat=95, critical=100),
            ]),
         ])

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
