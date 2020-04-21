
from . import InventoryInterface

class Temp(InventoryInterface):
   def getTemperature(self):
      raise NotImplementedError

   def getLowThreshold(self):
      raise NotImplementedError

   def getHighThreshold(self):
      raise NotImplementedError

   def setLowThreshold(self, value):
      raise NotImplementedError

   def setHighThreshold(self, value):
      raise NotImplementedError

   def __diag__(self, ctx):
      return {
         # TODO: SensorDesc info as self.desc.__diag__(ctx)
         "value": self.getTemperature() if ctx.performIo else None,
         "low_thresh": self.getLowThreshold(),
         "high_thresh": self.getHighThreshold(),
      }
