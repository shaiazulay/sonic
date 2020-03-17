
from __future__ import absolute_import, division, print_function

import logging
import time

from ..core.utils import getCmdlineDict
from ..core.platform import getSysEeprom

def readMacAddress(intfName):
   path = '/sys/class/net/%s/address' % intfName
   with open(path) as f:
      return f.read().rstrip()

def checkMgmtMacAddress(intfName='eth0'):
   currentMac = readMacAddress(intfName)
   desiredMac = getSysEeprom().get('MAC', '00:00:00:00:00:00')
   currentMacValue = int(currentMac.replace(':', ''), 16)
   desiredMacValue = int(desiredMac.replace(':', ''), 16)
   if currentMac == desiredMac:
      logging.info('mac address of %s is properly set to %s', intfName,
                   currentMac)
   elif currentMacValue == desiredMacValue + 1:
      logging.warning('mac address of %s is not set properly. is %s should be %s'
                      ' (likely coming from EOS via fast-reboot)',
                      intfName, currentMac, desiredMac)
   else:
      logging.error('mac address of %s is not set properly. is %s should be %s',
                    intfName, currentMac, desiredMac)
      for key, value in getCmdlineDict().items():
         if key.startswith('hwaddr_'):
            logging.info('cmdline: %s=%s', key, value)

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

   try:
      checkMgmtMacAddress()
   except:
      logging.error('failed to check mgmt mac address')

   while True:
      if hasSysCpld and not seuErrorDetected and platform.syscpld.hasSeuError():
         logging.error('A SEU error was detected')
         logging.info('The impact can vary from nothing and in rare cases unexpected behavior')
         logging.info('Power cycling the system would restore it to a clean slate')
         seuErrorDetected = True
      time.sleep(interval)
