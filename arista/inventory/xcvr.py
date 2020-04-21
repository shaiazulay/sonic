
class Xcvr(object):

   SFP = 0
   QSFP = 1
   OSFP = 2

   ADDR = 0x50

   @classmethod
   def typeStr(cls, typeIndex):
      return ['sfp', 'qsfp', 'osfp'][typeIndex]

   def getName(self):
      raise NotImplementedError()

   def getPresence(self):
      raise NotImplementedError()

   def getLowPowerMode(self):
      raise NotImplementedError()

   def setLowPowerMode(self, value):
      raise NotImplementedError()

   def getInterruptLine(self):
      raise NotImplementedError()

   def getReset(self):
      raise NotImplementedError()
