from ..core.platform import registerPlatform, Platform
from ..core.utils import incrange
from ..core.types import PciAddr, NamedGpio, ResetGpio
from ..core.component import Priority

from ..components.common import SwitchChip, I2cKernelComponent
from ..components.dpm import Ucd90120A, Ucd90160, UcdGpi, UcdMon
from ..components.fan import RavenFanCpldComponent
from ..components.psu import ScdPmbusPsu
from ..components.scd import Scd
from ..components.ds460 import Ds460

@registerPlatform('DCS-7050QX-32')
class Cloverdale(Platform):
   def __init__(self):
      super(Cloverdale, self).__init__()

      self.qsfp40gAutoRange = incrange(1, 24)
      self.qsfp40gOnlyRange = incrange(25, 32)
      self.allQsfps = sorted(self.qsfp40gAutoRange + self.qsfp40gOnlyRange)

      self.inventory.addPorts(qsfps=self.allQsfps)

      switchChip = SwitchChip(PciAddr(bus=0x02))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x04))
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      self.inventory.addPowerCycle(scd.createPowerCycle())

      ravenFanComponent = RavenFanCpldComponent(waitFile='/sys/class/hwmon/hwmon1')

      scd.addComponents([
         ravenFanComponent,
         I2cKernelComponent(scd.i2cAddr(0, 0x4c), 'max6658', '/sys/class/hwmon/hwmon2'),
         I2cKernelComponent(scd.i2cAddr(1, 0x48), 'lm73', '/sys/class/hwmon/hwmon3'),

         # Due to a risk of an unrecoverable firmware corruption when a pmbus
         # transaction is done at the same moment of the poweroff, the handling of
         # the DPM is disabled. If you want rail information use it at your own risk
         # The current implementation will just read the firmware information once.
         Ucd90120A(scd.i2cAddr(1, 0x4e), priority=Priority.BACKGROUND),
         Ucd90160(scd.i2cAddr(5, 0x4e), priority=Priority.BACKGROUND, causes={
            'reboot': UcdGpi(2),
            'watchdog': UcdGpi(3),
            'powerloss': UcdMon(13),
         }),
      ])

      for fanId in incrange(1, 4):
         self.inventory.addFan(ravenFanComponent.createFan(fanId))

      psu1Addr = scd.i2cAddr(3, 0x58)
      psu1 = Ds460(psu1Addr, '/sys/class/hwmon/hwmon4',
                   priority=Priority.BACKGROUND,
                   waitTimeout=30.0)
      psu2Addr = scd.i2cAddr(4, 0x58)
      psu2 = Ds460(psu2Addr, '/sys/class/hwmon/hwmon5',
                   priority=Priority.BACKGROUND,
                   waitTimeout=30.0)
      scd.addComponents([psu1, psu2])
      scd.addBusTweak(psu1Addr, 3, 3, 3, 1)
      scd.addBusTweak(psu2Addr, 3, 3, 3, 1)

      scd.addSmbusMasterRange(0x8000, 5)

      self.inventory.addLeds(scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ]))

      self.inventory.addResets(scd.addResets([
         ResetGpio(0x4000, 0, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 2, False, 'phy1_reset'),
         ResetGpio(0x4000, 3, False, 'phy2_reset'),
         ResetGpio(0x4000, 4, False, 'phy3_reset'),
         ResetGpio(0x4000, 5, False, 'phy4_reset'),
      ]))

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
      ])
      self.inventory.addPsus([
         ScdPmbusPsu(scd.createPsu(1, statusGpios=None), psu1),
         ScdPmbusPsu(scd.createPsu(2, statusGpios=None), psu2),
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

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
      ]

      addr = 0x5010
      bus = 8
      for xcvrId in self.allQsfps:
         intr = intrRegs[1].getInterruptBit(xcvrId - 1)
         name = 'qsfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         xcvr = scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                            leds=self.inventory.getLedGroup(name))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1
