
from .. import registerAction
from ...platform import doPlatform
from ....args.show.platform import showPlatformParser

@registerAction(showPlatformParser)
def doShowFabric(ctx, args):
   doPlatform(ctx, args)
