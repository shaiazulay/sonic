
from __future__ import absolute_import, division, print_function

from . import registerParser
from .platform import platformParser

@registerParser('clean', parent=platformParser,
                help='unload drivers for this platform')
def cleanParser(parser):
   parser.add_argument('-r', '--reset', action='store_true',
      help='put devices in reset before cleanup')
