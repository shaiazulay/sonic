
from __future__ import absolute_import, division, print_function

import os

from . import registerAction
from ..args.setup import setupParser
from ...core import utils
from ...core.config import Config
from ...core.component import Priority
from ...core.log import getLogger

logging = getLogger(__name__)

def forkForLateInitialization(platform):
   try:
      pid = os.fork()
   except OSError:
      logging.warn('fork failed, setting up background drivers normally')
   else:
      if pid > 0:
         logging.debug('initializing slow drivers in child %d', pid)
         platform.waitForIt()
         os._exit(0) # pylint: disable=protected-access

@registerAction(setupParser)
def doSetup(ctx, args):
   platform = ctx.platform

   if args.debug:
      utils.debug = True

   with utils.FileLock(Config().lock_file):
      logging.debug('setting up critical drivers')
      platform.setup(Priority.defaultFilter)

      # NOTE: This assumes that none of the resetable devices are
      #       initialized in background.
      #       This should stay true in the future.
      if args.reset:
         logging.debug('taking devices out of reset')
         platform.resetOut()

      if args.background:
         logging.debug('forking and setting up slow drivers in background')
         forkForLateInitialization(platform)
      else:
         logging.debug('setting up slow drivers normally')

      platform.setup(Priority.backgroundFilter)

      if not args.background:
         platform.waitForIt()
