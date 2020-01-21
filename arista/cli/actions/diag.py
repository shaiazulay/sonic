
from __future__ import absolute_import, division, print_function

import json

from . import registerAction
from ..args.diag import diagParser
from ...core.diag import DiagContext

@registerAction(diagParser)
def doDiag(ctx, args):
   diagCtx = DiagContext(
      performIo=not args.noIo,
      recursive=args.recursive,
   )
   diagInfo = []

   if args.recursive:
      diagInfo.append(ctx.platform.genDiag(diagCtx))
   else:
      for component in ctx.platform.iterComponents():
         diagInfo.append(component.genDiag(diagCtx))

   ident = 3 if args.pretty else None
   print(json.dumps(diagInfo, indent=ident))

