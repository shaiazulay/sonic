
from __future__ import absolute_import, division, print_function

import logging
import os
import time

from . import registerAction
from ...core import utils
from ...core.config import Config
from ...core.component import Priority

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

@registerAction('setup')
def doSetup(args, platform):
   if args.debug:
      utils.debug = True

   with utils.FileLock(Config().lock_file):
      logging.debug('setting up critical drivers')
      platform.setup(Priority.DEFAULT)

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

      platform.setup(Priority.BACKGROUND)

      if not args.background:
         platform.waitForIt()

@registerAction('clean')
def doClean(args, platform):
   if args.reset:
      logging.debug('putting devices in reset')
      platform.resetIn()

   logging.debug('cleaning up platform')
   with utils.FileLock(Config().lock_file):
      platform.clean()

@registerAction('reset')
def doReset(args, platform):
   resets = platform.getInventory().getResets()
   if args.reset_list:
      print('Reset Supported Devices:')
      print("{: <20} {: <20}".format('Name', 'Value'))
      for reset in sorted(resets):
         print("{: <20} {: <20}".format(reset, resets[reset].read()))
      return 1

   devices = args.device
   if not devices:
      devices = resets.keys()
   else:
      for device in devices:
         if device not in resets:
            logging.error('device %s does not exist', device)
            return 1

   if args.reset_out:
      for device in devices:
         resets[device].resetOut()
   elif args.reset_in:
      for device in devices:
         resets[device].resetIn()
   elif args.reset_toggle:
      for device in devices:
         resets[device].resetIn()
      time.sleep(args.reset_delay)
      for device in devices:
         resets[device].resetOut()
   else:
      logging.info('nothing to do')

   return 0
