
from ... import registerParser
from ...platform import platformParser
from ...show import showParser

@registerParser('platform', parent=showParser,
                help='Platform show commands')
def showPlatformParser(parser):
   platformParser(parser)
