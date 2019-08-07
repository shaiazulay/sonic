from ..core.platform import registerPlatform, Platform
from ..core.driver import KernelDriver
from ..core.utils import incrange
from ..core.types import PciAddr, NamedGpio, ResetGpio

from ..components.common import SwitchChip, I2cKernelComponent
from ..components.dpm import Ucd90120A, Ucd90160, UcdGpi
from ..components.fan import LAFanCpldComponent
from ..components.psu import PmbusPsu
from ..components.rook import RookLedComponent
from ..components.scd import Scd

@registerPlatform(['DCS-7170-64', 'DCS-7170-64C', 'DCS-7170-64C-SSD',
                   'DCS-7170-64C-M'])
class Alhambra(Platform):
   def __init__(self):
      super(Alhambra, self).__init__()

      self.qsfpRange = incrange(1, 64)
      self.sfpRange = incrange(65, 66)

      self.inventory.addPorts(qsfps=self.qsfpRange, sfps=self.sfpRange)

      self.addDriver(KernelDriver, 'rook-led-driver')

      switchChip = SwitchChip(PciAddr(bus=0x07))
      self.addComponent(switchChip)

      scd = Scd(PciAddr(bus=0x06), newDriver=True)
      self.addComponent(scd)

      self.inventory.addWatchdog(scd.createWatchdog())

      scd.addComponents([
         I2cKernelComponent(scd.i2cAddr(7, 0x4c), 'max6658',
                            '/sys/class/hwmon/hwmon2'),
         PmbusPsu(scd.i2cAddr(6, 0x58, t=3, datr=2, datw=3), name='dps1900'),
         PmbusPsu(scd.i2cAddr(5, 0x58, t=3, datr=2, datw=3), name='dps1900'),
      ])

      scd.addSmbusMasterRange(0x8000, 9, 0x80)

      self.inventory.addResets(scd.addResets([
         ResetGpio(0x4000, 8, False, 'switch_chip_reset'),
         ResetGpio(0x4000, 1, False, 'security_chip_reset'),
         ResetGpio(0x4000, 0, False, 'repeater_sfp_reset'),
      ]))

      scd.addGpios([
         NamedGpio(0x5000, 0, True, False, "psu1_present"),
         NamedGpio(0x5000, 1, True, False, "psu2_present"),
         NamedGpio(0x5000, 8, True, False, "psu1_status"),
         NamedGpio(0x5000, 9, True, False, "psu2_status"),
         NamedGpio(0x5000, 10, True, False, "psu1_ac_status"),
         NamedGpio(0x5000, 11, True, False, "psu2_ac_status"),
      ])

      ledComponent = RookLedComponent(baseName='rook_leds-96', scd=scd)

      self.addComponent(ledComponent)

      self.inventory.addLeds([
         ledComponent.createLed(colors=['blue'], name='beacon'),
         ledComponent.createLed(colors=['green', 'red'], name='fan_status'),
         ledComponent.createLed(colors=['green', 'red'], name='psu1_status'),
         ledComponent.createLed(colors=['green', 'red'], name='psu2_status'),
         ledComponent.createLed(colors=['green', 'red'], name='status'),
      ])

      self.inventory.addPsus([
         scd.createPsu(1, led=self.inventory.getLed('psu1_status')),
         scd.createPsu(2, led=self.inventory.getLed('psu2_status')),
      ])

      addr = 0x6100
      for xcvrId in self.qsfpRange:
         leds = []
         for laneId in incrange(1, 4):
            name = "qsfp%d_%d" % (xcvrId, laneId)
            leds.append(scd.addLed(addr, name))
            addr += 0x10
         self.inventory.addLedGroup("qsfp%d" % xcvrId, leds)

      addr = 0x7200
      for xcvrId in self.sfpRange:
         name = "sfp%d" % xcvrId
         self.inventory.addLedGroup(name, [scd.addLed(addr, name)])
         addr += 0x10

      scd.setMsiRearmOffset(0x190)

      intrRegs = [
         scd.createInterrupt(addr=0x3000, num=0, mask=0x60003ff),
         scd.createInterrupt(addr=0x3030, num=1),
         scd.createInterrupt(addr=0x3060, num=2),
      ]

      addr = 0xA010
      bus = 8
      for xcvrId in sorted(self.qsfpRange):
         intr = intrRegs[xcvrId // 33 + 1].getInterruptBit((xcvrId - 1) % 32)
         name = 'qsfp%d' % xcvrId
         self.inventory.addInterrupt(name, intr)
         xcvr = scd.addQsfp(addr, xcvrId, bus, interruptLine=intr,
                            leds=self.inventory.getLedGroup(name))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

      addr = 0xA500
      bus = 72
      for xcvrId in sorted(self.sfpRange):
         xcvr = scd.addSfp(addr, xcvrId, bus,
                           leds=self.inventory.getLedGroup('sfp%d' % xcvrId))
         self.inventory.addXcvr(xcvr)
         addr += 0x10
         bus += 1

      cpld = Scd(PciAddr(bus=0xff, device=0x0b, func=3), newDriver=True)
      self.addComponent(cpld)

      laFanCpldAddr = cpld.i2cAddr(12, 0x60)
      laFanComponent = LAFanCpldComponent(addr=laFanCpldAddr,
                                          waitFile='/sys/class/hwmon/hwmon4')

      for fanId in incrange(1, 4):
         self.inventory.addFan(laFanComponent.createFan(fanId))

      cpld.addSmbusMasterRange(0x8000, 4, 0x80, 4)
      cpld.addComponents([
         I2cKernelComponent(cpld.i2cAddr(0, 0x4c), 'max6658',
                            '/sys/class/hwmon/hwmon3'),
         Ucd90160(cpld.i2cAddr(1, 0x4e, t=3)),
         Ucd90120A(cpld.i2cAddr(10, 0x4e, t=3), causes={
            'powerloss': UcdGpi(1),
            'overtemp': UcdGpi(2),
            'reboot': UcdGpi(4),
            'watchdog': UcdGpi(5),
         }),
         laFanComponent,
         I2cKernelComponent(cpld.i2cAddr(15, 0x20), 'rook_leds'),
         I2cKernelComponent(cpld.i2cAddr(15, 0x48), 'lm73',
                            '/sys/class/hwmon/hwmon5')
      ])

      self.inventory.addPowerCycle(cpld.createPowerCycle())
