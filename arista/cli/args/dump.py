
from __future__ import absolute_import, division, print_function

from . import registerParser
from .platform import platformParser

@registerParser('dump', parent=platformParser,
                help='dump information on this platform')
def dumpParser(parser):
   pass
