from ..core.platform import registerPlatform, Platform
from ..core.utils import incrange
from ..core.types import I2cAddr, PciAddr, NamedGpio, ResetGpio
from ..core.component import Priority

from ..components.common import SwitchChip
from ..components.cpu.crow import CrowFanCpldComponent, CrowSysCpld
from ..components.dpm import Ucd90120A, UcdGpi
from ..components.max6658 import Max6658
from ..components.psu import PmbusMixedPsuComponent, PmbusPsu
from ..components.scd import Scd
from ..components.ds125br import Ds125Br

@registerPlatform()
class Clearlake(Platform):

   SID = ['Clearlake', 'ClearlakeSsd']
   SKU = ['DCS-7050QX-32S', 'DCS-7050QX-32S-SSD']

   def __init__(self):
      super(Clearlake, self).__init__()

      self.sfpRange = incrange(1, 4)
      self.qsfp40gAutoRange = incrange(5, 28)
      self.qsfp40gOnlyRange = incrange(29, 36)
      self.allQsfps = sorted(self.qsfp40gAutoRange + self.qsfp40gOnlyRange)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.allQsfps)

      self.newComponent(SwitchChip, PciAddr(bus=0x01))

      scd = self.newComponent(Scd, PciAddr(bus=0x02))

      self.inventory.addWatchdog(scd.createWatchdog())

      self.inventory.addPowerCycle(scd.createPowerCycle())

      scd.newComponent(Max6658, scd.i2cAddr(0, 0x4c),
                       waitFile='/sys/class/hwmon/hwmon2')
      scd.newComponent(Max6658, scd.i2cAddr(1, 0x4c),
                       waitFile='/sys/class/hwmon/hwmon3')

      crowFanCpldAddr = scd.i2cAddr(1, 0x60)
      crowFanComponent = scd.newComponent(CrowFanCpldComponent,
                                           addr=crowFanCpldAddr,
                                           waitFile='/sys/class/hwmon/hwmon4')

      for fanId in incrange(1, 4):
         self.inventory.addFan(crowFanComponent.createFan(fanId))

      scd.newComponent(Ucd90120A, scd.i2cAddr(1, 0x4e, t=3))
      scd.newComponent(Ucd90120A, scd.i2cAddr(5, 0x4e, t=3), causes={
         'reboot': UcdGpi(2),
         'watchdog': UcdGpi(3),
         'powerloss': UcdGpi(7),
      })
      scd.newComponent(Ds125Br, scd.i2cAddr(6, 0xff), priority=Priority.BACKGROUND)

      scd.addSmbusMasterRange(0x8000, 6)

      self.inventory.addLeds(scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ]))

      self.inventory.addReset(
         scd.addReset(ResetGpio(0x4000, 0, False, 'switch_chip_reset')))

      self.syscpld = self.newComponent(CrowSysCpld, I2cAddr(1, 0x23))

      pmbusPsu1 = scd.newComponent(PmbusPsu,
                                   scd.i2cAddr(3, 0x58, t=3, datr=3, datw=3),
                                   '/sys/class/hwmon/hwmon5')
      pmbusPsu2 = scd.newComponent(PmbusPsu,
                                   scd.i2cAddr(4, 0x58, t=3, datr=3, datw=3),
                                   '/sys/class/hwmon/hwmon6')
      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
         NamedGpio(0x6940, 0, False, False, "mux"), # FIXME: oldSetup order/name
      ])

      psu1 = scd.newComponent(PmbusMixedPsuComponent, presenceComponent=scd,
                              statusComponent=pmbusPsu1)
      psu2 = scd.newComponent(PmbusMixedPsuComponent, presenceComponent=scd,
                              statusComponent=pmbusPsu2)

      self.inventory.addPsus([
         psu1.createPsu(psuId=1, led=self.inventory.getLed('psu1')),
         psu2.createPsu(psuId=2, led=self.inventory.getLed('psu2')),
      ])

      addr = 0x6100
      for xcvrId in self.qsfp40gAutoRange:
         leds = []
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            leds.append(scd.addLed(addr, name))
            addr += 0x10
         self.inventory.addLedGroup("qsfp%d" % xcvrId, leds)

      addr = 0x6720
      for xcvrId in self.qsfp40gOnlyRange:
         name = "qsfp%d" % xcvrId
         self.inventory.addLedGroup(name, [scd.addLed(addr, name)])
         addr += 0x30 if xcvrId % 2 else 0x50

      addr = 0x6900
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         self.inventory.addLedGroup(name, [scd.addLed(addr, name)])
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
         xcvr = scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                            leds=self.inventory.getLedGroup(name))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

      addr = 0x5210
      bus = 40
      for xcvrId in sorted(self.sfpRange):
         xcvr = scd.addSfp(addr, xcvrId, bus,
                           leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

@registerPlatform()
class ClearlakePlus(Clearlake):
   SID = ['ClearlakePlus', 'ClearlakePlusSsd']
   SKU = ['DCS-7050QX2-32S', 'DCS-7050QX2-32S-SSD']

