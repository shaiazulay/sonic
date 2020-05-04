
from .. import registerParser
from ..default import defaultPlatformParser

@registerParser('show', parent=defaultPlatformParser,
                help='Show commands')
def showParser(parser):
   parser.add_argument('-j', '--json', action='store_true',
      help='output library information in json format')
