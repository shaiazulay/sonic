
from .component import Component
from .utils import HwApi

class Sku(Component):

   PLATFORM = None
   SID = None
   SKU = None

   DEFAULT_HWAPI = '0'

   def __init__(self, hwApi=None, *args, **kwargs):
      super(Sku, self).__init__(*args, **kwargs)
      self.hwApi = hwApi

   def getEeprom(self):
      return {}

   def getHwApi(self):
      if not self.hwApi:
         self.hwApi = HwApi(self.getEeprom().get('HwApi', self.DEFAULT_HWAPI))
      return self.hwApi

   def genDiag(self, ctx):
      output = super(Sku, self).genDiag(ctx)
      output['eeprom'] = self.getEeprom() if ctx.performIo else None
      return output
