from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.utils import incrange
from ..core.types import PciAddr, NamedGpio, ResetGpio

from ..components.asic.xgs.tomahawk2 import Tomahawk2
from ..components.coretemp import Coretemp
from ..components.cpu.intel.pch import Pch
from ..components.cpu.rook import LAFanCpldComponent
from ..components.dpm import Ucd90120A, Ucd90160, UcdGpi
from ..components.max6658 import Max6658
from ..components.psu import PmbusPsu
from ..components.scd import Scd

from ..descs.psu import PsuDesc
from ..descs.sensor import Position, SensorDesc

from .cpu.rook import RookCpu

@registerPlatform()
class Gardena(FixedSystem):

   SID = ['Gardena', 'GardenaE']
   SKU = ['DCS-7260CX3-64', 'DCS-7260CX3-64E']

   def __init__(self):
      super(Gardena, self).__init__()

      self.sfpRange = incrange(65, 66)
      self.qsfpRange = incrange(1, 64)

      self.inventory.addPorts(qsfps=self.qsfpRange, sfps=self.sfpRange)

      self.newComponent(Tomahawk2, PciAddr(bus=0x07))

      scd = self.newComponent(Scd, PciAddr(bus=0x06))
      self.scd = scd

      scd.createWatchdog()

      self.newComponent(Pch, sensors=[
         SensorDesc(diode=0, name='PCH temp sensor',
                    position=Position.OTHER, target=65, overheat=75, critical=85),
      ])

      self.newComponent(Coretemp, sensors=[
         SensorDesc(diode=0, name='Physical id 0',
                    position=Position.OTHER, target=82, overheat=95, critical=105),
         SensorDesc(diode=1, name='CPU core0 temp sensor',
                    position=Position.OTHER, target=82, overheat=95, critical=105),
         SensorDesc(diode=2, name='CPU core1 temp sensor',
                    position=Position.OTHER, target=82, overheat=95, critical=105),
      ])

      scd.newComponent(Max6658, scd.i2cAddr(0, 0x4c),
                       waitFile='/sys/class/hwmon/hwmon2', sensors=[
         SensorDesc(diode=0, name='Board sensor',
                    position=Position.OTHER, target=65, overheat=75, critical=85),
      ])

      scd.addSmbusMasterRange(0x8000, 8, 0x80)

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
      ])

      cpu = self.newComponent(RookCpu, fanCpldCls=LAFanCpldComponent)
      cpu.cpld.newComponent(Ucd90160, cpu.cpuDpmAddr())
      cpu.cpld.newComponent(Ucd90120A, cpu.switchDpmAddr(0x34), causes={
         'powerloss': UcdGpi(1),
         'reboot': UcdGpi(2),
         'watchdog': UcdGpi(3),
         'overtemp': UcdGpi(4),
      })
      self.cpu = cpu
      self.syscpld = cpu.syscpld

      for psuId in incrange(1, 2):
         scd.addPsu(PmbusPsu, addr=scd.i2cAddr(1 + psuId, 0x58, t=3, datr=2, datw=3),
                    waitFile="/sys/class/hwmon/hwmon%d" % (5 + psuId),
                    psus=[
            PsuDesc(psuId=psuId,
                    led=cpu.leds.inventory.getLed('psu%d_status' % psuId), sensors=[
               SensorDesc(diode=0,
                          name='Power supply %d hotspot sensor' % psuId,
                          position=Position.OTHER,
                          target=80, overheat=95, critical=100),
               SensorDesc(diode=1,
                          name='Power supply %d inlet temp sensor' % psuId,
                          position=Position.INLET,
                          target=55, overheat=70, critical=75),
               SensorDesc(diode=2,
                          name='Power supply %d exhaust temp sensor' % psuId,
                          position=Position.OUTLET,
                          target=80, overheat=108, critical=113),
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

      addr = 0x7100
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x10

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xA010
      bus = 8
      for xcvrId in sorted(self.qsfpRange):
         intr = intrRegs[xcvrId // 33 + 1].getInterruptBit((xcvrId - 1) % 32)
         name = 'qsfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

      addr = 0xA410
      bus = 6
      for xcvrId in sorted(self.sfpRange):
         scd.addSfp(addr, xcvrId, bus,
                    leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         addr += 0x10
         bus += 1
