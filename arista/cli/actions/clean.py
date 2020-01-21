
from __future__ import absolute_import, division, print_function

import logging

from . import registerAction
from ...core import utils
from ...core.config import Config

@registerAction('clean')
def doClean(args, platform):
   if args.reset:
      logging.debug('putting devices in reset')
      platform.resetIn()

   logging.debug('cleaning up platform')
   with utils.FileLock(Config().lock_file):
      platform.clean()
