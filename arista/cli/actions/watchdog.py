
from __future__ import absolute_import, division, print_function

import logging

from . import registerAction

@registerAction('watchdog')
def doWatchdog(args, platform):
   watchdog = platform.getInventory().getWatchdog()
   if args.watchdog_status:
      st = watchdog.status()
      if st:
         kv = ' '.join('%s=%s' % (k, v) for k, v in st.items())
         print("Watchdog status: %s" % kv)
      else:
         print("Watchdog status - error.")
         return 1
   elif args.watchdog_stop:
      logging.info('disabling the hardware watchdog')
      if not watchdog.stop():
         logging.error('failed to stop the hardware watchdog')
         return 1
   else:
      logging.info('arming the hardware watchdog for %ds', args.watchdog_timeout)
      # Tens of milliseconds
      watchdog_timeout = args.watchdog_timeout * 100
      if watchdog_timeout >= 65536:
         logging.error('failed to arm the hardware watchdog: time value is too big')
         return 1
      if not watchdog.arm(watchdog_timeout):
         logging.error('failed to arm the hardware watchdog')
         return 1
   return 0

