
from __future__ import absolute_import, division, print_function

from . import registerAction
from ...core.platform import getSysEeprom

@registerAction('syseeprom', needsPlatform=False)
def doSysEeprom(args, platform):
   for key, value in getSysEeprom().items():
      print('%s: %s' % (key, value))
