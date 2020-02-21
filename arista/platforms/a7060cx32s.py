from ..core.platform import registerPlatform, Platform
from ..core.utils import incrange
from ..core.types import PciAddr, I2cAddr, NamedGpio, ResetGpio

from ..components.common import SwitchChip
from ..components.cpu.crow import CrowSysCpld, CrowFanCpldComponent
from ..components.dpm import Ucd90120A, UcdGpi
from ..components.max6658 import Max6658
from ..components.max6697 import Max6697
from ..components.psu import UpperlakeMixedPsuComponent, PmbusPsu
from ..components.scd import Scd

@registerPlatform()
class Upperlake(Platform):

   SID = ['Upperlake', 'UpperlakeES', 'UpperlakeSsd']
   SKU = ['DCS-7060CX-32S', 'DCS-7060CX-32S-ES', 'DCS-7060CX-32S-SSD']

   def __init__(self):
      super(Upperlake, self).__init__()

      self.sfpRange = incrange(33, 34)
      self.qsfp100gRange = incrange(1, 32)

      self.inventory.addPorts(sfps=self.sfpRange, qsfps=self.qsfp100gRange)

      switchChip = SwitchChip(PciAddr(bus=0x01))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x02))
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      crowFanCpldAddr = scd.i2cAddr(1, 0x60)
      crowFanComponent = CrowFanCpldComponent(addr=crowFanCpldAddr,
                                              waitFile='/sys/class/hwmon/hwmon4')

      for fanId in incrange(1, 4):
         self.inventory.addFan(crowFanComponent.createFan(fanId))

      scd.addComponents([
         Max6697(scd.i2cAddr(0, 0x1a), waitFile='/sys/class/hwmon/hwmon2'),
         Max6658(scd.i2cAddr(1, 0x4c), waitFile='/sys/class/hwmon/hwmon3'),
         crowFanComponent,
         Ucd90120A(scd.i2cAddr(1, 0x4e, t=3)),
         PmbusPsu(scd.i2cAddr(3, 0x58, t=3, datr=2, datw=3)),
         PmbusPsu(scd.i2cAddr(4, 0x58, t=3, datr=2, datw=3)),
         Ucd90120A(scd.i2cAddr(5, 0x4e, t=3), causes={
            'reboot': UcdGpi(1),
            'watchdog': UcdGpi(2),
            'overtemp': UcdGpi(4),
            'powerloss': UcdGpi(5),
         }),
      ])

      scd.addSmbusMasterRange(0x8000, 5, 0x80)

      self.inventory.addLeds(scd.addLeds([
         (0x6050, 'status'),
         (0x6060, 'fan_status'),
         (0x6070, 'psu1'),
         (0x6080, 'psu2'),
         (0x6090, 'beacon'),
      ]))

      self.inventory.addResets(scd.addResets([
         ResetGpio(0x4000, 1, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 2, False, 'switch_chip_pcie_reset'),
      ]))

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
      ])

      self.syscpld = CrowSysCpld(I2cAddr(1, 0x23))
      cpld = self.syscpld
      self.inventory.addPowerCycle(cpld.createPowerCycle())
      self.addComponent(cpld)

      psuComponent = UpperlakeMixedPsuComponent(presenceComponent=scd,
                                                statusComponent=cpld)

      self.addComponent(psuComponent)

      self.inventory.addPsus([
         psuComponent.createPsu(psuId=1, led=self.inventory.getLed('psu1')),
         psuComponent.createPsu(psuId=2, led=self.inventory.getLed('psu2')),
      ])

      addr = 0x6100
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         self.inventory.addLedGroup(name, [scd.addLed(addr, name)])
         addr += 0x10

      addr = 0x6140
      for xcvrId in self.qsfp100gRange:
         leds = []
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            leds.append(scd.addLed(addr, name))
            addr += 0x10
         self.inventory.addLedGroup("qsfp%d" % xcvrId, leds)

      addr = 0x5010
      bus = 8
      for xcvrId in self.sfpRange:
         xcvr = scd.addSfp(addr, xcvrId, bus,
                           leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0),
         scd.createInterrupt(addr=0x3030, num=1),
      ]

      addr = 0x5050
      bus = 16
      for xcvrId in self.qsfp100gRange:
         intr = intrRegs[1].getInterruptBit(xcvrId - 1)
         name = 'qsfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         xcvr = scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                            leds=self.inventory.getLedGroup(name))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

