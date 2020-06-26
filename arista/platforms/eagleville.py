
from ..core.fixed import FixedSystem
from ..core.platform import registerPlatform
from ..core.utils import incrange

@registerPlatform()
class Eagleville(FixedSystem):

   SID = ['Eagleville']
   SKU = ['DCS-7050CX3M-32S']

   def __init__(self):
      super(Eagleville, self).__init__()

      self.qsfpRange = incrange(1, 32)
      self.sfpRange = incrange(33, 34)

      self.inventory.addPorts(qsfps=self.qsfpRange, sfps=self.sfpRange)
