# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..core.inventory import Phy

class PhyImpl(Phy):
   def __init__(self, phyId, reset=None):
      self.id = phyId
      self.reset = reset

   def getReset(self):
      return self.reset

class MdioPhy(PhyImpl):
   def __init__(self, phyId, mdios, reset=None):
      super(MdioPhy, self).__init__(phyId, reset=reset)
      self.mdios = mdios

   def getMdios(self):
      return self.mdios

class Babbage(MdioPhy):
   pass
