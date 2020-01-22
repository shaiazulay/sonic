
from __future__ import absolute_import, division, print_function

import logging
import time

def runDaemon(platform, interval=60):
   hasSysCpld = False
   seuErrorDetected = False

   logging.info('starting arista daemon')

   if hasattr(platform, 'syscpld'):
      hasSysCpld = True
      if platform.syscpld.powerCycleOnSeu():
         logging.info('disabling powercycle on SEU')
         platform.syscpld.powerCycleOnSeu(False)
      else:
         logging.info('powercycle on SEU already disabled')

   while True:
      if hasSysCpld and not seuErrorDetected and platform.syscpld.hasSeuError():
         logging.error('A SEU error was detected')
         logging.info('The impact can vary from nothing and in rare cases unexpected behavior')
         logging.info('Power cycling the system would restore it to a clean slate')
         seuErrorDetected = True
      time.sleep(interval)
