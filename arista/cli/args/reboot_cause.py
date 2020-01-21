
from __future__ import absolute_import, division, print_function

from . import registerParser

@registerParser('reboot-cause', help='reload cause information',
                 description='''
Read last reboot information from the hardware and display it.
''')
def rebootCauseParser( parser ):
   parser.add_argument('--history', action='store_true',
      help='print reboot causes history if it exists')
