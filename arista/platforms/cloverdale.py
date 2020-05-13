from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.types import PciAddr, NamedGpio, ResetGpio
from ..core.utils import incrange

from ..components.asic.xgs.trident2 import Trident2
from ..components.cpu.raven import RavenFanCpldComponent
from ..components.dpm import Ucd90120A, Ucd90160, UcdGpi, UcdMon
from ..components.cpu.amd.k10temp import K10Temp
from ..components.lm73 import Lm73
from ..components.max6658 import Max6658
from ..components.scd import Scd
from ..components.ds460 import Ds460

from ..descs.fan import FanDesc
from ..descs.psu import PsuDesc
from ..descs.sensor import Position, SensorDesc

@registerPlatform()
class Cloverdale(FixedSystem):

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

      self.newComponent(Trident2, PciAddr(bus=0x02))

      scd = self.newComponent(Scd, PciAddr(bus=0x04))

      scd.createWatchdog()

      scd.createPowerCycle()

      self.newComponent(K10Temp, sensors=[
         SensorDesc(diode=0, name='Cpu temp sensor',
                    position=Position.OTHER, target=62, overheat=95, critical=100),
      ])

      scd.newComponent(RavenFanCpldComponent, waitFile='/sys/class/hwmon/hwmon1',
                       fans=[
         FanDesc(fanId) for fanId in incrange(1, 4)
      ])

      scd.newComponent(Max6658, scd.i2cAddr(0, 0x4c),
                       waitFile='/sys/class/hwmon/hwmon2', sensors=[
         SensorDesc(diode=0, name='Board sensor',
                    position=Position.OTHER, target=36, overheat=55, critical=70),
         SensorDesc(diode=1, name='Front-panel temp sensor',
                    position=Position.INLET, target=42, overheat=65, critical=75),
      ])
      scd.newComponent(Lm73, scd.i2cAddr(1, 0x48),
                       waitFile='/sys/class/hwmon/hwmon3', sensors=[
         SensorDesc(diode=0, name='Rear temp sensor',
                    position=Position.OUTLET, target=42, overheat=65, critical=75),
      ])
      # Due to a risk of an unrecoverable firmware corruption when a pmbus
      # transaction is done at the same moment of the poweroff, the handling of
      # the DPM is disabled. If you want rail information use it at your own risk
      # The current implementation will just read the firmware information once.
      self.newComponent(Ucd90120A, scd.i2cAddr(1, 0x4e, t=3))
      self.newComponent(Ucd90160, scd.i2cAddr(5, 0x4e, t=3), causes={
         'reboot': UcdGpi(2),
         'watchdog': UcdGpi(3),
         'powerloss': UcdMon(13),
      })

      scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ])

      # PSU
      for psuId in incrange(1, 2):
         scd.addPsu(Ds460,
                    addr=scd.i2cAddr(2 + psuId, 0x58, t=3, datr=3, datw=3, ed=0),
                    waitFile='/sys/class/hwmon/hwmon%d' % (3 + psuId), psus=[
            PsuDesc(psuId=psuId, led=self.inventory.getLed('psu%d' % psuId),
                    sensors=[
               SensorDesc(diode=0, name='Power supply %d inlet temp sensor' % psuId,
                          position=Position.INLET,
                          target=39, overheat=60, critical=70),
               SensorDesc(diode=1, name='Power supply %d internal sensor' % psuId,
                          position=Position.OTHER,
                          target=55, overheat=80, critical=150),
            ]),
         ])

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
      ])

      scd.addSmbusMasterRange(0x8000, 5)

      scd.addResets([
         ResetGpio(0x4000, 0, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 2, False, 'phy1_reset'),
         ResetGpio(0x4000, 3, False, 'phy2_reset'),
         ResetGpio(0x4000, 4, False, 'phy3_reset'),
         ResetGpio(0x4000, 5, False, 'phy4_reset'),
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
         scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                     leds=self.inventory.getLedGroup(name))
         addr += 0x10
         bus += 1
