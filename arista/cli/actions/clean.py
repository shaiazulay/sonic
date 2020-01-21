
from __future__ import absolute_import, division, print_function

import logging

from . import registerAction
from ..args.clean import cleanParser
from ...core import utils
from ...core.config import Config

@registerAction(cleanParser)
def doClean(ctx, args):
   if args.reset:
      logging.debug('putting devices in reset')
      ctx.platform.resetIn()

   logging.debug('cleaning up platform')
   with utils.FileLock(Config().lock_file):
      ctx.platform.clean()
