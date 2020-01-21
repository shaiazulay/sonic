
from __future__ import absolute_import, division, print_function

from . import registerAction

@registerAction('dump')
def doDump(args, platform):
   platform.dump()
