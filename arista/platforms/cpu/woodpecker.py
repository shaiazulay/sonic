from ...core.cpu import Cpu
from ...core.types import PciAddr
from ...core.utils import incrange

from ...components.fan import ScdFanComponent
from ...components.max6658 import Max6658
from ...components.scd import Scd

from ...descs.fan import FanDesc
from ...descs.sensor import Position, SensorDesc

class WoodpeckerCpu(Cpu):

   PLATFORM = 'woodpecker'

   def __init__(self, hwmonOffset=2, **kwargs):
      super(WoodpeckerCpu, self).__init__(**kwargs)

      cpld = self.newComponent(Scd, PciAddr(bus=0x00, device=0x09, func=0))
      self.cpld = cpld

      waitFile = '/sys/class/hwmon/hwmon%d' % hwmonOffset
      self.scdFanComponent = cpld.newComponent(ScdFanComponent, waitFile=waitFile,
                                               fans=[
         FanDesc(fanId, ledId=(fanId - 1) / 2 + 1) for fanId in incrange(1, 6)
      ])
      cpld.addFanGroup(0x9000, 3, 3)

      cpld.addSmbusMasterRange(0x8000, 2, 0x80, 4)
      cpld.newComponent(Max6658, cpld.i2cAddr(0, 0x4c),
                        waitFile='/sys/class/hwmon/hwmon%d' % (hwmonOffset + 1),
                        sensors=[
         SensorDesc(diode=0, name='CPU board temp sensor',
                    position=Position.OTHER, target=55, overheat=75, critical=85),
         SensorDesc(diode=1, name='Back-panel temp sensor',
                    position=Position.OUTLET, target=55, overheat=75, critical=85),
      ])

      cpld.createPowerCycle()

   def cpuDpmAddr(self, addr=0x4e, t=3, **kwargs):
      return self.cpld.i2cAddr(1, addr, t=t, **kwargs)

   def switchDpmAddr(self, addr=0x11, t=3, **kwargs):
      return self.cpld.i2cAddr(5, addr, t=t, **kwargs)
