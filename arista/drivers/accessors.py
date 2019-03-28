from __future__ import print_function, with_statement

from ..core.inventory import Fan, Psu, Reset, Xcvr

class PsuImpl(Psu):
   def __init__(self, driver=None, **kwargs):
      self.driver = driver
      self.statusGpio = True
      self.__dict__.update(kwargs)

   def getPresence(self):
      return self.driver.getPsuPresence(self)

   def getStatus(self):
      return self.driver.getPsuStatus(self)

class XcvrImpl(Xcvr):
   def __init__(self, driver=None, interruptLine=None, reset=None, **kwargs):
      self.driver = driver
      self.interruptLine = interruptLine
      self.reset = reset
      typeStr = Xcvr.typeStr(kwargs['xcvrType'])
      self.name = '%s%s' % (typeStr, kwargs['xcvrId'])
      self.__dict__.update(kwargs)

   def getPresence(self):
      return self.driver.getXcvrPresence(self)

   def getLowPowerMode(self):
      return self.driver.getXcvrLowPowerMode(self)

   def setLowPowerMode(self, value):
      return self.driver.setXcvrLowPowerMode(self, value)

   def getModuleSelect(self):
      return self.driver.getXcvrModuleSelect(self)

   def setModuleSelect(self, value):
      return self.driver.setXcvrModuleSelect(self, value)

   def getTxDisable(self):
      return self.driver.getXcvrTxDisable(self)

   def setTxDisable(self, value):
      return self.driver.setXcvrTxDisable(self, value)

   def getInterruptLine(self):
      return self.interruptLine

   def getReset(self):
      return self.reset

class ResetImpl(Reset):
   def __init__(self, name=None, driver=None, **kwargs):
      self.name = name
      self.driver = driver
      self.__dict__.update(kwargs)

   def read(self):
      return self.driver.readReset(self)

   def resetIn(self):
      return self.driver.resetComponentIn(self)

   def resetOut(self):
      return self.driver.resetComponentOut(self)

   def getName(self):
      return self.name

class FanImpl(Fan):
   def __init__(self, driver=None, **kwargs):
      self.driver = driver
      self.__dict__.update(kwargs)

   def getSpeed(self):
      return self.driver.getFanSpeed(self)

   def setSpeed(self, speed):
      return self.driver.setFanSpeed(self, speed)

   def getDirection(self):
      return self.driver.getFanDirection(self)
