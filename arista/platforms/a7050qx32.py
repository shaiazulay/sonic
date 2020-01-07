from ..core.platform import registerPlatform, Platform
from ..core.utils import incrange
from ..core.types import PciAddr, NamedGpio, ResetGpio

from ..components.common import SwitchChip
from ..components.dpm import Ucd90120A, Ucd90160, UcdGpi, UcdMon
from ..components.fan import RavenFanCpldComponent
from ..components.lm73 import Lm73
from ..components.max6658 import Max6658
from ..components.psu import PmbusMixedPsuComponent
from ..components.scd import Scd
from ..components.ds460 import Ds460

@registerPlatform()
class Cloverdale(Platform):

   # This platform doesn't have sid= on the cmdline and therefore needs to rely
   # on platform= instead. Alternatively we rely on SKU
   PLATFORM = 'raven'
   SID = ['Cloverdale', 'CloverdaleSsd']
   SKU = ['DCS-7050QX-32']

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
         Max6658(scd.i2cAddr(0, 0x4c), waitFile='/sys/class/hwmon/hwmon2'),
         Lm73(scd.i2cAddr(1, 0x48), waitFile='/sys/class/hwmon/hwmon3'),
         # Due to a risk of an unrecoverable firmware corruption when a pmbus
         # transaction is done at the same moment of the poweroff, the handling of
         # the DPM is disabled. If you want rail information use it at your own risk
         # The current implementation will just read the firmware information once.
         Ucd90120A(scd.i2cAddr(1, 0x4e, t=3)),
         Ucd90160(scd.i2cAddr(5, 0x4e, t=3), causes={
            'reboot': UcdGpi(2),
            'watchdog': UcdGpi(3),
            'powerloss': UcdMon(13),
         }),
      ])

      for fanId in incrange(1, 4):
         self.inventory.addFan(ravenFanComponent.createFan(fanId))

      self.inventory.addLeds(scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ]))

      # PSU
      psu1Addr = scd.i2cAddr(3, 0x58, t=3, datr=3, datw=3, ed=0)
      ds460Psu1 = Ds460(psu1Addr, '/sys/class/hwmon/hwmon4')
      psu2Addr = scd.i2cAddr(4, 0x58, t=3, datr=3, datw=3, ed=0)
      ds460Psu2 = Ds460(psu2Addr, '/sys/class/hwmon/hwmon5')
      scd.addComponents([ds460Psu1, ds460Psu2])

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
      ])

      psu1 = PmbusMixedPsuComponent(presenceComponent=scd,
                                    statusComponent=ds460Psu1)
      psu2 = PmbusMixedPsuComponent(presenceComponent=scd,
                                    statusComponent=ds460Psu2)

      self.addComponents([psu1, psu2])

      self.inventory.addPsus([
         psu1.createPsu(psuId=1, led=self.inventory.getLed('psu1')),
         psu2.createPsu(psuId=2, led=self.inventory.getLed('psu2')),
      ])

      scd.addSmbusMasterRange(0x8000, 5)

      self.inventory.addResets(scd.addResets([
         ResetGpio(0x4000, 0, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 2, False, 'phy1_reset'),
         ResetGpio(0x4000, 3, False, 'phy2_reset'),
         ResetGpio(0x4000, 4, False, 'phy3_reset'),
         ResetGpio(0x4000, 5, False, 'phy4_reset'),
      ]))

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
