
from __future__ import absolute_import, division, print_function

from . import registerParser
from .platform import platformParser

@registerParser('daemon', parent=platformParser,
                help='run arista daemon to monitor the hardware')
def daemonParser(parser):
   parser.add_argument('-f', '--feature', action='append',
      help='Name of the features to run, default all')
