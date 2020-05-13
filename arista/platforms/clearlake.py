from ..core.component import Priority
from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.types import I2cAddr, PciAddr, NamedGpio, ResetGpio
from ..core.utils import incrange

from ..components.asic.xgs.trident2 import Trident2
from ..components.cpu.crow import CrowFanCpldComponent, CrowSysCpld
from ..components.dpm import Ucd90120A, UcdGpi
from ..components.cpu.amd.k10temp import K10Temp
from ..components.max6658 import Max6658
from ..components.psu import PmbusPsu
from ..components.scd import Scd
from ..components.ds125br import Ds125Br

from ..descs.fan import FanDesc
from ..descs.psu import PsuDesc
from ..descs.sensor import Position, SensorDesc

@registerPlatform()
class Clearlake(FixedSystem):

   SID = ['Clearlake', 'ClearlakeSsd']
   SKU = ['DCS-7050QX-32S', 'DCS-7050QX-32S-SSD']

   def __init__(self):
      super(Clearlake, self).__init__()

      self.sfpRange = incrange(1, 4)
      self.qsfp40gAutoRange = incrange(5, 28)
      self.qsfp40gOnlyRange = incrange(29, 36)
      self.allQsfps = sorted(self.qsfp40gAutoRange + self.qsfp40gOnlyRange)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.allQsfps)

      self.newComponent(Trident2, PciAddr(bus=0x01))

      scd = self.newComponent(Scd, PciAddr(bus=0x02))

      scd.createWatchdog()

      scd.createPowerCycle()

      self.newComponent(K10Temp, sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=60, overheat=90, critical=95),
      ])

      scd.newComponent(Max6658, scd.i2cAddr(0, 0x4c),
                       waitFile='/sys/class/hwmon/hwmon2', sensors=[
         SensorDesc(diode=0, name='Board Sensor',
                    position=Position.OTHER, target=36, overheat=55, critical=70),
         SensorDesc(diode=1, name='Front-panel temp sensor',
                    position=Position.INLET, target=42, overheat=65, critical=75),
      ])
      scd.newComponent(Max6658, scd.i2cAddr(1, 0x4c),
                       waitFile='/sys/class/hwmon/hwmon3', sensors=[
         SensorDesc(diode=0, name='Cpu board temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=80),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=50, overheat=75, critical=80),
      ])

      scd.newComponent(CrowFanCpldComponent, addr=scd.i2cAddr(1, 0x60),
                       waitFile='/sys/class/hwmon/hwmon4', fans=[
         FanDesc(fanId) for fanId in incrange(1, 4)
      ])

      scd.newComponent(Ucd90120A, scd.i2cAddr(1, 0x4e, t=3))
      scd.newComponent(Ucd90120A, scd.i2cAddr(5, 0x4e, t=3), causes={
         'reboot': UcdGpi(2),
         'watchdog': UcdGpi(3),
         'powerloss': UcdGpi(7),
      })
      scd.newComponent(Ds125Br, scd.i2cAddr(6, 0xff), priority=Priority.BACKGROUND)

      scd.addSmbusMasterRange(0x8000, 6)

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])

      scd.addReset(ResetGpio(0x4000, 0, False, 'switch_chip_reset'))

      self.syscpld = self.newComponent(CrowSysCpld, I2cAddr(1, 0x23))

      for psuId in incrange(1, 2):
         scd.addPsu(PmbusPsu, addr=scd.i2cAddr(2 + psuId, 0x58, t=3, datr=3, datw=3),
                    waitFile='/sys/class/hwmon/hwmon%d' % (4 + psuId), psus=[
            PsuDesc(psuId=psuId, led=self.inventory.getLed('psu%d' % psuId),
                    sensors=[
               SensorDesc(diode=0, name='Power supply %d hotspot sensor' % psuId,
                          position=Position.OTHER,
                          target=80, overheat=95, critical=100),
               SensorDesc(diode=1, name='Power supply %d inlet temp sensor' % psuId,
                          position=Position.INLET,
                          target=55, overheat=70, critical=75),
               SensorDesc(diode=2, name='Power supply %d sensor' % psuId,
                          position=Position.OTHER,
                          target=80, overheat=108, critical=113),
            ]),
         ])

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
         NamedGpio(0x6940, 0, False, False, "mux"), # FIXME: oldSetup order/name
      ])

      addr = 0x6100
      for xcvrId in self.qsfp40gAutoRange:
         leds = []
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            leds.append((addr, name))
            addr += 0x10
         scd.addLedGroup("qsfp%d" % xcvrId, leds)

      addr = 0x6720
      for xcvrId in self.qsfp40gOnlyRange:
         name = "qsfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x30 if xcvrId % 2 else 0x50

      addr = 0x6900
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         scd.addLedGroup(name, [(addr, name)])
         addr += 0x10

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
      ]

      addr = 0x5010
      bus = 8
      for xcvrId in self.allQsfps:
         intr = intrRegs[1].getInterruptBit(xcvrId - 5)
         name = 'qsfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1

      addr = 0x5210
      bus = 40
      for xcvrId in sorted(self.sfpRange):
         scd.addSfp(addr, xcvrId, bus,
                    leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         addr += 0x10
         bus += 1

@registerPlatform()
class ClearlakePlus(Clearlake):
   SID = ['ClearlakePlus', 'ClearlakePlusSsd']
   SKU = ['DCS-7050QX2-32S', 'DCS-7050QX2-32S-SSD']
