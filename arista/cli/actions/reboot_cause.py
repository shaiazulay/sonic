
from __future__ import absolute_import, division, print_function

from . import registerAction
from ...core import utils
from ...core.cause import (
   getReloadCause,
   getReloadCauseHistory,
   updateReloadCausesHistory
)
from ...core.config import Config

@registerAction('reboot-cause')
def doRebootCause(args, platform):
   if utils.inSimulation():
      return
   with utils.FileLock(Config().lock_file):
      updateReloadCausesHistory(platform.getReloadCauses(clear=True))
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
