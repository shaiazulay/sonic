from ..core.platform import registerPlatform, Platform
from ..core.utils import incrange
from ..core.types import I2cAddr, PciAddr, NamedGpio, ResetGpio
from ..core.component import Priority

from ..components.common import SwitchChip, I2cKernelComponent
from ..components.cpld import SysCpld
from ..components.dpm import Ucd90120A, UcdGpi
from ..components.fan import CrowFanCpldComponent
from ..components.psu import PmbusMixedPsuComponent, PmbusPsu
from ..components.scd import Scd
from ..components.ds125br import Ds125Br

@registerPlatform(['DCS-7050QX-32S', 'Clearlake'])
class Clearlake(Platform):
   def __init__(self):
      super(Clearlake, self).__init__()

      self.sfpRange = incrange(1, 4)
      self.qsfp40gAutoRange = incrange(5, 28)
      self.qsfp40gOnlyRange = incrange(29, 36)
      self.allQsfps = sorted(self.qsfp40gAutoRange + self.qsfp40gOnlyRange)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.allQsfps)

      switchChip = SwitchChip(PciAddr(bus=0x01))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x02))
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      self.inventory.addPowerCycle(scd.createPowerCycle())

      crowFanCpldAddr = scd.i2cAddr(1, 0x60)
      crowFanComponent = CrowFanCpldComponent(addr=crowFanCpldAddr,
                                              waitFile='/sys/class/hwmon/hwmon4')

      for fanId in incrange(1, 4):
         self.inventory.addFan(crowFanComponent.createFan(fanId))

      scd.addComponents([
         I2cKernelComponent(scd.i2cAddr(0, 0x4c), 'max6658',
                            '/sys/class/hwmon/hwmon2'),
         I2cKernelComponent(scd.i2cAddr(1, 0x4c), 'max6658',
                            '/sys/class/hwmon/hwmon3'),
         crowFanComponent,
         Ucd90120A(scd.i2cAddr(1, 0x4e, t=3)),
         Ucd90120A(scd.i2cAddr(5, 0x4e, t=3), causes={
            'reboot': UcdGpi(2),
            'watchdog': UcdGpi(3),
            'powerloss': UcdGpi(7),
         }),
         Ds125Br(scd.i2cAddr(6, 0xff), priority=Priority.BACKGROUND),
      ])

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

      pmbusPsu1 = PmbusPsu(scd.i2cAddr(3, 0x58, t=3, datr=3, datw=3),
                           '/sys/class/hwmon/hwmon5')
      pmbusPsu2 = PmbusPsu(scd.i2cAddr(4, 0x58, t=3, datr=3, datw=3),
                           '/sys/class/hwmon/hwmon6')
      scd.addComponents([pmbusPsu1, pmbusPsu2])
      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
         NamedGpio(0x6940, 0, False, False, "mux"), # FIXME: oldSetup order/name
      ])

      psu1 = PmbusMixedPsuComponent(presenceComponent=scd,
                                    statusComponent=pmbusPsu1)
      psu2 = PmbusMixedPsuComponent(presenceComponent=scd,
                                    statusComponent=pmbusPsu2)

      self.addComponents([psu1, psu2])

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

      self.syscpld = SysCpld(I2cAddr(1, 0x23),
         seuCfgReg=0x09,
         seuCfgBit=0,
         seuStsReg=0x0a,
         seuStsBit=2,
      )

@registerPlatform('DCS-7050QX2-32S')
class ClearlakePlus(Clearlake):
   pass

