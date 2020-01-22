
from __future__ import absolute_import, division, print_function

from . import registerAction
from ..args.platforms import platformsParser
from ...core.platform import getPlatformSkus, Platform

@registerAction(platformsParser, needsPlatform=False)
def doPlatforms(ctx, args):
   print('supported platforms:')
   for plat, cls in sorted(getPlatformSkus().items()):
      if issubclass(cls, Platform):
         print(' -', plat)
