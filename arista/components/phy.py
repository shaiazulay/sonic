# Copyright (c) 2018 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from ..core.inventory import Phy

class PhyImpl( Phy ):
   def __init__( self, phyId, reset=None ):
      self.id = phyId
      self.reset = reset

   def getReset( self ):
      return self.reset

class MdioPhy( PhyImpl ):
   def __init__( self, phyId, reset=None, mdio=None ):
      super( MdioPhy, self ).__init__( phyId, reset=reset )
      self.mdio = mdio

   def getMdio( self ):
      return self.mdio

