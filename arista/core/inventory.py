from collections import defaultdict

# NOTE: users of inventory should reference the appropriate file directly
#       these imports are a backward compatibility layer only
# pylint: disable=unused-import
from ..inventory.fan import Fan
from ..inventory.interrupt import Interrupt
from ..inventory.led import Led
from ..inventory.phy import Phy
from ..inventory.powercycle import PowerCycle
from ..inventory.psu import Psu
from ..inventory.reloadcause import ReloadCause
from ..inventory.reset import Reset
from ..inventory.slot import Slot
from ..inventory.temp import Temp
from ..inventory.watchdog import Watchdog
from ..inventory.xcvr import Xcvr

class Inventory(object):
   def __init__(self):
      self.sfpRange = []
      self.qsfpRange = []
      self.osfpRange = []
      self.allXcvrsRange = []

      self.portStart = None
      self.portEnd = None

      self.leds = {}
      self.ledGroups = {}

      self.xcvrs = {}

      # These two are deprecated
      self.xcvrLeds = defaultdict(list)
      self.statusLeds = []

      self.psus = []

      self.fans = []

      self.watchdog = Watchdog()

      self.powerCycles = []

      self.interrupts = {}

      self.resets = {}

      self.phys = []

      self.slots = []

      self.temps = []

   def freeze(self):
      # XXX: compute the range and some basic information from the various
      #      collections present in the inventory
      # XXX: try to avoid that actually
      pass

   def addPorts(self, sfps=None, qsfps=None, osfps=None):
      if sfps:
         self.sfpRange = sfps
      if qsfps:
         self.qsfpRange = qsfps
      if osfps:
         self.osfpRange = osfps

      self.allXcvrsRange = sorted(self.sfpRange + self.qsfpRange +
                                  self.osfpRange)
      self.portStart = self.allXcvrsRange[0]
      self.portEnd = self.allXcvrsRange[-1]

   def addXcvr(self, xcvr):
      self.xcvrs[xcvr.xcvrId] = xcvr
      xcvrReset = xcvr.getReset()
      if xcvrReset is not None:
         self.resets[xcvrReset.getName()] = xcvrReset

   def getXcvrs(self):
      return self.xcvrs

   def getXcvr(self, xcvrId):
      return self.xcvrs[xcvrId]

   def getPortToEepromMapping(self):
      eepromPath = '/sys/class/i2c-adapter/i2c-{0}/{0}-{1:04x}/eeprom'
      return { xcvrId : eepromPath.format(xcvr.addr.bus, xcvr.addr.address)
               for xcvrId, xcvr in self.xcvrs.items() }

   def getPortToI2cAdapterMapping(self):
      return { xcvrId : xcvr.addr.bus for xcvrId, xcvr in self.xcvrs.items() }

   # Deprecated
   def addXcvrLed(self, xcvrId, name):
      self.xcvrLeds[xcvrId].append(name)

   # Deprecated
   def addStatusLed(self, name):
      self.statusLeds.append(name)

   # Deprecated
   def addStatusLeds(self, names):
      self.statusLeds.extend(names)

   def addLed(self, led):
      self.leds[led.getName()] = led

   def addLedGroup(self, name, leds):
      self.ledGroups[name] = leds
      for led in leds:
         self.addLed(led)

   def addLeds(self, leds):
      for led in leds:
         self.addLed(led)

   def getLed(self, name):
      return self.leds[name]

   def getLedGroup(self, name):
      return self.ledGroups[name]

   def getLeds(self):
      return self.leds

   def getLedGroups(self):
      return self.ledGroups

   def addPsus(self, psus):
      self.psus.extend(psus)

   def getPsus(self):
      return self.psus

   def getPsu(self, index):
      return self.psus[index]

   def getNumPsus(self):
      return len(self.psus)

   def addFan(self, fan):
      self.fans.append(fan)

   def addFans(self, fans):
      self.fans.extend(fans)

   def getFan(self, index):
      return self.fans[index]

   def getFans(self):
      return self.fans

   def getNumFans(self):
      return len(self.fans)

   def addWatchdog(self, watchdog):
      self.watchdog = watchdog

   def getWatchdog(self):
      return self.watchdog

   def addPowerCycle(self, powerCycle):
      self.powerCycles.append(powerCycle)

   def getPowerCycles(self):
      return self.powerCycles

   def addInterrupt(self, name, interrupt):
      self.interrupts[name] = interrupt

   def addInterrupts(self, interrupts):
      self.interrupts.update(interrupts)

   def getInterrupts(self):
      return self.interrupts

   def addReset(self, reset):
      self.resets[reset.getName()] = reset

   def addResets(self, resets):
      self.resets.update(resets)

   def getResets(self):
      return self.resets

   def addPhy(self, phy):
      self.phys.append(phy)

   def getPhys(self):
      return self.phys

   def addSlot(self, slot):
      self.slots.append(slot)

   def getSlots(self):
      return self.slots

   def addTemp(self, temp):
      self.temps.append(temp)

   def getTemps(self):
      return self.temps
