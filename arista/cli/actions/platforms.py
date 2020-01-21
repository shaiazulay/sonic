
from __future__ import absolute_import, division, print_function

from . import registerAction
from ..args.platforms import platformsParser
from ...core.platform import getPlatformSkus

@registerAction(platformsParser, needsPlatform=False)
def doPlatforms(ctx, args):
   print('supported platforms:')
   for plat in sorted(getPlatformSkus()):
      print(' -', plat)
