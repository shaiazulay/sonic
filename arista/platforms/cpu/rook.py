from ...core.cpu import Cpu
from ...core.types import PciAddr
from ...core.utils import incrange

from ...components.scd import Scd
from ...components.cpu.rook import RookStatusLeds, RookSysCpld
from ...components.lm73 import Lm73
from ...components.max6658 import Max6658

from ...descs.fan import FanDesc
from ...descs.led import LedDesc

class RookCpu(Cpu):

   PLATFORM = 'rook'

   def __init__(self, hwmonOffset=3, fanCount=4, fanCpldCls=None, mgmtBus=15,
                **kwargs):
      super(RookCpu, self).__init__(**kwargs)
      cpld = self.newComponent(Scd, PciAddr(bus=0xff, device=0x0b, func=3))
      self.cpld = cpld

      cpld.addSmbusMasterRange(0x8000, 4, 0x80, 4)
      cpld.newComponent(Max6658, cpld.i2cAddr(0, 0x4c),
                        waitFile='/sys/class/hwmon/hwmon%d' % hwmonOffset)
      cpld.newComponent(fanCpldCls, cpld.i2cAddr(12, 0x60),
                        waitFile='/sys/class/hwmon/hwmon%d' % (hwmonOffset + 1),
                        fans=[
         FanDesc(fanId) for fanId in incrange(1, fanCount)
      ])

      cpld.newComponent(Lm73, cpld.i2cAddr(mgmtBus, 0x48),
                        waitFile='/sys/class/hwmon/hwmon%d' % (hwmonOffset + 2))

      self.leds = cpld.newComponent(RookStatusLeds, cpld.i2cAddr(mgmtBus, 0x20),
                                    leds=[
         LedDesc(name='beacon', colors=['blue']),
         LedDesc(name='fan_status', colors=['green', 'red']),
         LedDesc(name='psu1_status', colors=['green', 'red']),
         LedDesc(name='psu2_status', colors=['green', 'red']),
         LedDesc(name='status', colors=['green', 'red']),
      ])

      cpld.createPowerCycle()

      self.syscpld = self.newComponent(RookSysCpld, cpld.i2cAddr(8, 0x23))

   def cpuDpmAddr(self, addr=0x4e, t=3, **kwargs):
      return self.cpld.i2cAddr(1, addr, t=t, **kwargs)

   def switchDpmAddr(self, addr=0x4e, t=3, **kwargs):
      return self.cpld.i2cAddr(10, addr, t=t, **kwargs)
