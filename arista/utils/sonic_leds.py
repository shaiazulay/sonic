from collections import defaultdict

from .sonic_utils import getInventory, parsePortConfig

# DO NOT REMOVE THIS LINE. Needed to import all the platform info.
import arista.platforms

try:
   from sonic_led import led_control_base
except ImportError as e:
   raise ImportError('%s - required module not found' % str(e))

class LedControl(led_control_base.LedControlBase):
   LED_SYSFS_PATH = "/sys/class/leds/{0}/brightness"

   LED_COLOR_OFF = 0
   LED_COLOR_GREEN = 1
   LED_COLOR_YELLOW = 2

   def __init__(self):
      self.portMapping = parsePortConfig()
      self.portSysfsMapping = defaultdict(list)

      inventory = getInventory()
      for port, names in inventory.xcvrLeds.items():
         for name in names:
            self.portSysfsMapping[port].append(self.LED_SYSFS_PATH.format(name))

      # Set status leds to green initially (Rook led driver does this automatically)
      for statusLed in inventory.statusLeds:
         with open(self.LED_SYSFS_PATH.format(statusLed), 'w') as fp:
            fp.write('%d' % self.LED_COLOR_GREEN)

   def port_link_state_change(self, port, state):
      '''
      Looks up the port in the port mapping to determine the front number and how
      many subsequent LEDs should be affected (hardcoded by the port_config)
      '''
      p = self.portMapping.get(port)
      if not p:
         return
      for idx in range(p.lanes):
         path = self.portSysfsMapping[p.portNum][idx]
         with open(path, 'w') as fp:
            if state == 'up':
               if idx == 0:
                  fp.write('%d' % self.LED_COLOR_GREEN)
               else:
                  fp.write('%d' % self.LED_COLOR_YELLOW)
            elif state == 'down':
               fp.write('%d' % self.LED_COLOR_OFF)
         if p.singular:
            return

def getLedControl():
   return LedControl
