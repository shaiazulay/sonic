from __future__ import print_function, with_statement

import os

from ..core.driver import Driver

class SysfsDriver(Driver):
   def __init__(self, sysfsPath=None, **kwargs):
      super(SysfsDriver, self).__init__(sysfsPath=sysfsPath, **kwargs)

   def read(self, name):
      with open(os.path.join(self.sysfsPath, name), 'r') as f:
         return f.read().rstrip()

   def getPsuPresence(self, psu):
      return self.read('psu%d_%s' % (psu.psuId, psu.presenceGpios)) == '1'

   def getPsuStatus(self, psu):
      if psu.statusGpios:
         return self.read('psu%d_%s' % (psu.psuId, psu.statusGpios)) == '1'
      return self.getPsuPresence(psu)

   def __str__(self):
      return '%s(%s)' % (self.__class__.__name__, self.sysfsPath)
