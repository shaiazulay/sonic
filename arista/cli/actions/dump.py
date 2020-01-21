
from __future__ import absolute_import, division, print_function

from . import registerAction
from ...core.platform import (
   getSysEeprom,
   getPlatformSkus,
)

@registerAction('platforms', needsPlatform=False)
def doPlatforms(args, platform):
   print('supported platforms:')
   for plat in sorted(getPlatformSkus()):
      print(' -', plat)

@registerAction('syseeprom', needsPlatform=False)
def doSysEeprom(args, platform):
   for key, value in getSysEeprom().items():
      print('%s: %s' % (key, value))

@registerAction('dump')
def doDump(args, platform):
   platform.dump()
