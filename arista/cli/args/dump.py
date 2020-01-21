
from __future__ import absolute_import, division, print_function

from . import registerParser

@registerParser('platforms', help='show supported platforms')
def platformsParser(parser):
   pass

@registerParser('syseeprom', help='show system eeprom content')
def syseepromParser(parser):
   pass

@registerParser('dump', help='dump information on this platform')
def dump(parser):
   pass
