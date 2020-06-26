
from __future__ import absolute_import, division, print_function

from . import registerParser
from .default import defaultPlatformParser

@registerParser('dump', parent=defaultPlatformParser,
                help='dump information on this platform')
def dumpParser(parser):
   pass
