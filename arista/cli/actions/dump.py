
from __future__ import absolute_import, division, print_function

from . import registerAction
from ..args.dump import dumpParser

@registerAction(dumpParser)
def doDump(ctx, args):
   ctx.platform.dump()
