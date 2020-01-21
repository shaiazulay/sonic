
from __future__ import absolute_import, division, print_function

from . import registerAction
from ...core.platform import getPlatformSkus

@registerAction('platforms', needsPlatform=False)
def doPlatforms(args, platform):
   print('supported platforms:')
   for plat in sorted(getPlatformSkus()):
      print(' -', plat)
