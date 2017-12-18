# DO NOT REMOVE THIS LINE. Needed to import all the platform info.
import arista.platforms

from collections import defaultdict

from arista.utils.sonic_utils import parsePortConfig, getSonicVersVar
from ..core import platform

try:
   from sonic_led import led_control_base
except ImportError as e:
   raise ImportError('%s - required module not found' % str(e))

class LedControlCommon(led_control_base.LedControlBase):
   LED_COLOR_OFF = None
   LED_COLOR_GREEN = None
   LED_COLOR_YELLOW = None

   def __init__(self):
      self.portMapping = parsePortConfig()
      self.inventory = platform.getPlatform().getInventory()
      # Set status leds to green initially (Rook led driver does this automatically)
      for statusLed in self.inventory.statusLeds:
         self._setStatusColor(statusLed, self.LED_COLOR_GREEN)

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
   LED_COLOR_YELLOW = 2

   def __init__(self):
      LedControlCommon.__init__(self)
      self.portSysfsMapping = defaultdict(list)
      for port, names in self.inventory.xcvrLeds.items():
         for name in names:
            self.portSysfsMapping[port].append(self.LED_SYSFS_PATH.format(name))

   def _setStatusColor(self, invStatusLed, color):
      with open(self.LED_SYSFS_PATH.format(invStatusLed), 'w') as fp:
         fp.write('%d' % self.LED_COLOR_GREEN)

   def _setIntfColor(self, port, idx, color):
      path = self.portSysfsMapping[port.portNum][port.offset + idx]
      with open(path, 'w') as fp:
         fp.write('%d' % color)

class LedControlCeos(LedControlCommon):
   LED_COLOR_OFF = 'off'
   LED_COLOR_GREEN = 'green'
   LED_COLOR_YELLOW = 'yellow'

   def __init__(self):
      from jsonrpclib import Server
      self.ceos = Server("http://localhost:8080/command-api)")
      #TODO: add status and check fan_status equivalent in EOS
      self.invToCliStatusLedMap = {'status' : 'status',
                                   'fan_status' : 'fantray',
                                   'psu(?P<num>\d+' : 'powersupply',
                                   'beacon' : 'chassis'}
      LedControlCommon.__init__(self)

   def _setStatusColor(self, invStatusLed, color):
      # TODO: map this to cEOS CLI calls.
      pass

   def _setIntfColor(self, port, idx, color):
      ceosIntfName = "Ethernet%d" % port.portNum
      if not port.singular:
         ceosIntfName = "%s/%s" % (ceosIntfName, idx + 1)
      try:
         self.ceos.runCmds(1,
                           ['enable', 'led interface %s %s' % (ceosIntfName, color)])
      except:
         pass
      return

def getLedControl():
   if getSonicVersVar('asic_type') == 'ceos':
      return LedControlCeos
   return LedControlSysfs
