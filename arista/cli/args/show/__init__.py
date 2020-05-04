
from .. import registerParser
from ..platform import platformParser

@registerParser('show', parent=platformParser,
                help='Show commands')
def showParser(parser):
   parser.add_argument('-j', '--json', action='store_true',
      help='output library information in json format')
