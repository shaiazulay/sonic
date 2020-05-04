
from __future__ import absolute_import, division, print_function

from . import registerParser
from .default import defaultPlatformParser

@registerParser('diag', parent=defaultPlatformParser,
                help='dump diag information on this platform')
def diagParser(parser):
   parser.add_argument('-n', '--noIo', action='store_true',
      help='do not perform any IO to generate the diag info')
   parser.add_argument('-r', '--recursive', action='store_true',
      help='generate a recursive output rather than a flat one')
   parser.add_argument('-p', '--pretty', action='store_true',
      help='generate a pretty json output')
   parser.add_argument('--pyshell', action='store_true',
      help='start a pyshell instead of printing output')
