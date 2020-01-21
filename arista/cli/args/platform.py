
from __future__ import absolute_import, division, print_function

from . import registerParser

@registerParser('setup', help='setup drivers for this platform')
def setupParser(parser):
   parser.add_argument('-r', '--reset', action='store_true',
      help='put devices out of reset after init')
   parser.add_argument('-d', '--debug', action='store_true',
      help='enable debug features for the drivers')
   parser.add_argument('-b', '--background', action='store_true',
      help='initialize slow, non-critical drivers in background')

@registerParser('clean', help='unload drivers for this platform')
def cleanParser(parser):
   parser.add_argument('-r', '--reset', action='store_true',
     help='put devices in reset before cleanup')

@registerParser('reset', help='put devices in or out reset')
def resetParser(parser):
   parser.add_argument('device', nargs='*',
      help='device(s) to put in or out of reset')
   parser.add_argument('-t', '--toggle', action='store_true', dest='reset_toggle',
      help='put devices in and out of reset')
   parser.add_argument('-i', '--in', action='store_true', dest='reset_in',
      help='put devices in reset')
   parser.add_argument('-o', '--out', action='store_true', dest='reset_out',
      help='put devices out of reset')
   parser.add_argument('-d', '--delay', type=int, default=1, dest='reset_delay',
      help='time to wait between in and out in seconds')
   parser.add_argument('-l', '--list', action='store_true', dest='reset_list',
      help='list devices that support reset')
