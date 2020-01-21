
from __future__ import absolute_import, division, print_function

import os
import sys

from . import registerAction
from ..args.platform import platformParser
from ...core import utils
from ...core.platform import getPlatform
from ...core.log import getLogger

logging = getLogger(__name__)

def checkRootPermissions():
   if utils.inSimulation():
      return

   if os.geteuid() != 0:
      logging.error('You must be root to use this feature')
      sys.exit(1)

@registerAction(platformParser)
def doPlatform(ctx, args):
   checkRootPermissions()
   platform = getPlatform(args.platform)
   setattr(ctx, 'platform', platform)
