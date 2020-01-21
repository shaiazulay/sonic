
from __future__ import absolute_import, division, print_function

from . import registerAction
from ..args.reboot_cause import rebootCauseParser
from ...core import utils
from ...core.cause import (
   getReloadCause,
   getReloadCauseHistory,
   updateReloadCausesHistory
)
from ...core.config import Config

@registerAction(rebootCauseParser)
def doRebootCause(ctx, args):
   if utils.inSimulation():
      return
   with utils.FileLock(Config().lock_file):
      updateReloadCausesHistory(ctx.platform.getReloadCauses(clear=True))
   if args.history:
      causes = getReloadCauseHistory()
   else:
      causes = getReloadCause()
   if not causes:
      print('No reboot cause detected')
      return
   print('Found reboot cause(s):')
   print('----------------------')
   for item in causes:
      print(item)
