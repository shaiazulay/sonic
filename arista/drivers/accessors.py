from __future__ import print_function, with_statement

from ..core.inventory import Psu, Reset, Xcvr

class PsuImpl(Psu):
   def __init__(self, **kwargs):
      self.statusGpio = True
      self.__dict__.update(kwargs)

   def getPresence(self):
      return self.driver.getPsuPresence(self)

   def getStatus(self):
      return self.driver.getPsuStatus(self)

class XcvrImpl(Xcvr):
   def __init__(self, **kwargs):
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
   def __init__(self, **kwargs):
      self.__dict__.update(kwargs)

   def read(self):
      return self.driver.readReset(self)

   def resetIn(self):
      return self.driver.resetComponentIn(self)

   def resetOut(self):
      return self.driver.resetComponentOut(self)

   def getName(self):
      return self.name
