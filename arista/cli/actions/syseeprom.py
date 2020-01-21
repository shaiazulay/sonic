
from __future__ import absolute_import, division, print_function

from . import registerAction
from ..args.syseeprom import syseepromParser
from ...core.platform import getSysEeprom

@registerAction(syseepromParser)
def doSysEeprom(ctx, args):
   for key, value in getSysEeprom().items():
      print('%s: %s' % (key, value))
