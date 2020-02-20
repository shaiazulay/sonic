
from __future__ import absolute_import, division, print_function

from ..core.daemon import registerDaemonFeature, PollDaemonFeature
from ..core.log import getLogger

logging = getLogger(__name__)

@registerDaemonFeature()
class SeuDaemonFeature(PollDaemonFeature):

   NAME = 'seu'
   INTERVAL = 60

   @classmethod
   def runnable(cls, daemon):
      return hasattr(daemon.platform, 'syscpld')

   def init(self):
      PollDaemonFeature.init(self)
      self.seuErrorDetected = False
      if self.daemon.platform.syscpld.powerCycleOnSeu():
         logging.info('disabling powercycle on SEU')
         self.daemon.platform.syscpld.powerCycleOnSeu(False)
      else:
         logging.info('powercycle on SEU already disabled')

   def callback(self, elapsed):
      if not self.seuErrorDetected and self.daemon.platform.syscpld.hasSeuError():
         logging.error('A SEU error was detected')
         logging.info('The impact can vary from nothing and in rare cases '
                      'unexpected behavior')
         logging.info('Power cycling the system would restore it to a clean slate')
         self.seuErrorDetected = True
