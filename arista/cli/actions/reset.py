
from __future__ import absolute_import, division, print_function

import logging
import time

from . import registerAction

@registerAction('reset')
def doReset(args, platform):
   resets = platform.getInventory().getResets()
   if args.reset_list:
      print('Reset Supported Devices:')
      print("{: <20} {: <20}".format('Name', 'Value'))
      for reset in sorted(resets):
         print("{: <20} {: <20}".format(reset, resets[reset].read()))
      return 1

   devices = args.device
   if not devices:
      devices = resets.keys()
   else:
      for device in devices:
         if device not in resets:
            logging.error('device %s does not exist', device)
            return 1

   if args.reset_out:
      for device in devices:
         resets[device].resetOut()
   elif args.reset_in:
      for device in devices:
         resets[device].resetIn()
   elif args.reset_toggle:
      for device in devices:
         resets[device].resetIn()
      time.sleep(args.reset_delay)
      for device in devices:
         resets[device].resetOut()
   else:
      logging.info('nothing to do')

   return 0
