from __future__ import absolute_import

from arista.utils.sonic_ceos_utils import ceosManagesPsus, CeosCli

from ..core import platform as core_platform
from .. import platforms

try:
   from sonic_psu.psu_base import PsuBase
except ImportError as e:
   raise ImportError("%s - required module not found" % str(e))


def getPsuUtil():
   platform = core_platform.getPlatform()
   inventory = platform.getInventory()

   class PsuUtil(PsuBase):
      """Platform-specific PsuUtil class"""

      def get_psu_presence(self, index):
         if index > inventory.getNumPsus() and index > 0:
            return False

         return inventory.getPsu(index-1).getPresence()

      def get_psu_status(self, index):
         if index > inventory.getNumPsus() and index > 0:
            return False

         return inventory.getPsu(index-1).getStatus()

      def get_num_psus(self):
         return inventory.getNumPsus()

   class PsuUtilCeos(PsuBase):
      """PsuUtil for cEOS on SONiC"""

      def __init__(self):
         self.ceos = CeosCli()

      def get_psu_presence(self, index):
         psus = self.ceos.getCmdJson('show environment power', 'powerSupplies')
         return str(index) in psus

      def get_psu_status(self, index):
         psus = self.ceos.getCmdJson('show environment power', 'powerSupplies')
         return psus.get(str(index), {}).get('state') == 'ok'

      def get_num_psus(self):
         return len(self.ceos.getCmdJson('show inventory', 'powerSupplySlots'))

   if ceosManagesPsus():
      return PsuUtilCeos
   return PsuUtil
