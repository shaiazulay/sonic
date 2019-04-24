from collections import defaultdict
import re

from .sonic_utils import getInventory, parsePortConfig

try:
   from sonic_led import led_control_base # pylint: disable=F0401
except ImportError as e:
   raise ImportError('%s - required module not found' % str(e))

class LedControlCommon(led_control_base.LedControlBase):
   LED_COLOR_OFF = None
   LED_COLOR_GREEN = None
   LED_COLOR_YELLOW = None

   def __init__(self):
      self.portMapping = parsePortConfig()
      self.inventory = getInventory()
      # Set status leds to green initially (Rook led driver does this automatically)
      for led in self.inventory.getLeds().values():
         if led.isStatusLed():
            self._setStatusColor(led.getName(), self.LED_COLOR_GREEN)

   def _setStatusColor(self, invStatusLed, color):
      raise NotImplementedError('Missing override of _setStatusColor')

   def _setIntfColor(self, port, idx, color):
      raise NotImplementedError('Missing override of _setIntfColor')

   def port_link_state_change(self, port, state):
      '''
      Looks up the port in the port mapping to determine the front number and how
      many subsequent LEDs should be affected (hardcoded by the port_config)
      '''
      p = self.portMapping.get(port)
      if not p:
         return
      for idx in range(p.lanes):
         if state == 'up':
            if idx == 0:
               self._setIntfColor(p, idx, self.LED_COLOR_GREEN)
            else:
               self._setIntfColor(p, idx, self.LED_COLOR_YELLOW)
         elif state == 'down':
            self._setIntfColor(p, idx, self.LED_COLOR_OFF)
         if p.singular:
            return

class LedControlSysfs(LedControlCommon):
   LED_SYSFS_PATH = "/sys/class/leds/{0}/brightness"

   LED_COLOR_OFF = 0
   LED_COLOR_GREEN = 1
   LED_COLOR_YELLOW = 3

   def __init__(self):
      LedControlCommon.__init__(self)
      self.portSysfsMapping = defaultdict(list)
      for xcvr in self.inventory.getXcvrs().values():
         for led in xcvr.getLeds():
            ledName = led.getName()
            port = int(re.search(r'\d+', ledName).group(0))
            self.portSysfsMapping[port].append(self.LED_SYSFS_PATH.format(ledName))

   def _setStatusColor(self, invStatusLed, color):
      with open(self.LED_SYSFS_PATH.format(invStatusLed), 'w') as fp:
         fp.write('%d' % color)

   def _setIntfColor(self, port, idx, color):
      portList = self.portSysfsMapping[port.portNum]
      offset = port.offset
      if 'osfp' in portList[0]:
         # OSFP only has one led
         if idx != 0:
            return
         offset = 0
      path = portList[idx + offset]
      with open(path, 'w') as fp:
         fp.write('%d' % color)

def getLedControl():
   return LedControlSysfs
