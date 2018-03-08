from collections import defaultdict
import logging

from .utils import simulateWith

class Xcvr(object):

   SFP = 0
   QSFP = 1

   ADDR = 0x50

   def __init__(self, portNum, xcvrType, addr):
      self.portNum = portNum
      self.xcvrType = xcvrType
      self.addr = addr

   def getPresence(self):
      raise NotImplementedError()

   def getLowPowerMode(self):
      raise NotImplementedError()

   def setLowPowerMode(self, value):
      raise NotImplementedError()

   def getInterruptLine(self):
      raise NotImplementedError()

   def reset(self, value):
      raise NotImplementedError()

class Psu(object):
   def getPresence(self):
      raise NotImplementedError()

   def getStatus(self):
      raise NotImplementedError()

class Watchdog(object):
   def armSim(self, timeout):
      logging.info("watchdog arm")
      return True

   @simulateWith(armSim)
   def arm(self, timeout):
      raise NotImplementedError()

   def stopSim(self):
      logging.info("watchdog stop")
      return True

   @simulateWith(stopSim)
   def stop(self):
      raise NotImplementedError()

   def statusSim(self):
      logging.info("watchdog status")
      return { "enabled": True, "timeout": 300 }

   @simulateWith(statusSim)
   def status(self):
      raise NotImplementedError()

class PowerCycle(object):
   def powerCycle(self):
      raise NotImplementedError()

class Interrupt(object):
   def set(self):
      raise NotImplementedError()

   def clear(self):
      raise NotImplementedError()

   def getFile(self):
      raise NotImplementedError()

class Reset(object):
   def read(self):
      raise NotImplementedError()

   def resetIn(self):
      raise NotImplementedError()

   def resetOut(self):
      raise NotImplementedError()

   def getName(self):
      raise NotImplementedError()

class Inventory(object):
   def __init__(self):
      self.sfpRange = []
      self.qsfpRange = []
      self.allXcvrsRange = []

      self.portStart = None
      self.portEnd = None

      self.xcvrs = {}

      self.xcvrLeds = defaultdict(list)
      self.statusLeds = []

      self.psus = []

      self.watchdog = Watchdog()

      self.powerCycles = []

      self.interrupts = {}

      self.resets = {}

   def freeze(self):
      # XXX: compute the range and some basic information from the various
      #      collections present in the inventory
      # XXX: try to avoid that actually
      pass

   def addPorts(self, sfps=None, qsfps=None):
      if sfps:
         self.sfpRange = sfps
      if qsfps:
         self.qsfpRange = qsfps

      self.allXcvrsRange = sorted(self.sfpRange + self.qsfpRange)
      self.portStart = self.allXcvrsRange[0]
      self.portEnd = self.allXcvrsRange[-1]

   def addXcvr(self, xcvr):
      self.xcvrs[xcvr.portNum] = xcvr

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

   def addXcvrLed(self, xcvrId, name):
      self.xcvrLeds[xcvrId].append(name)

   def addStatusLed(self, name):
      self.statusLeds.append(name)

   def addStatusLeds(self, names):
      self.statusLeds.extend(names)

   def addPsus(self, psus):
      self.psus = psus

   def getPsu(self, index):
      return self.psus[index]

   def getNumPsus(self):
      return len(self.psus)

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
