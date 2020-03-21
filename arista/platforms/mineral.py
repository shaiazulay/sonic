from ..core.platform import registerPlatform
from .alhambra import Alhambra

@registerPlatform()
class Mineral(Alhambra):

   SID = ['Mineral', 'MineralSsd']
   SKU = ['DCS-7170-32C', 'DCS-7170-32C-M']

   def __init__(self):
      super(Mineral, self).__init__(ports=32)

@registerPlatform()
class MineralD(Mineral):

   SID = ['MineralD']
   SKU = ['DCS-7170-32CD']
