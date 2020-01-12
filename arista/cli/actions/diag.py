
from __future__ import absolute_import, division, print_function

import json

from . import registerAction
from ...core.diag import DiagContext

@registerAction('diag')
def doDiag(args, platform):
   ctx = DiagContext(
      performIo=not args.noIo,
      recursive=args.recursive,
   )
   diagInfo = []

   if args.recursive:
      diagInfo.append(platform.genDiag(ctx))
   else:
      for component in platform.iterComponents():
         diagInfo.append(component.genDiag(ctx))

   ident = 3 if args.pretty else None
   print(json.dumps(diagInfo, indent=ident))

