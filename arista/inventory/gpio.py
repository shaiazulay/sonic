from . import InventoryInterface

class Gpio(InventoryInterface):
   def getName(self):
      raise NotImplementedError()

   def getAddr(self):
      raise NotImplementedError()

   def getPath(self):
      raise NotImplementedError()

   def getBit(self):
      raise NotImplementedError()

   def isRo(self):
      raise NotImplementedError()

   def isActiveLow(self):
      raise NotImplementedError()

   def getRawValue(self):
      raise NotImplementedError()

   def isActive(self):
      raise NotImplementedError()

   def setActive(self, value):
      raise NotImplementedError()

   def __diag__(self, ctx):
      diagDict = {
         "name": self.getName(),
         "addr": hex(self.getAddr()),
         "path": self.getPath(),
         "bit": self.getBit(),
         "ro": self.isRo(),
         "activeLow": self.isActiveLow(),
      }

      if ctx.performIo:
         diagDict.update({
            "rawValue": self.getRawValue(),
            "active": self.isActive(),
         })

      return diagDict
