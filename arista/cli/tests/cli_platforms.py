from __future__ import absolute_import

from multiprocessing import Process

from ...tests.testing import unittest, patch
from ...core.platform import loadPlatforms, getPlatforms
from .. import main

class CliLegacyTest(unittest.TestCase):
   def _runMain(self, args, code=0):
      p = Process(target=main, args=(args,))
      p.start()
      p.join()
      self.assertEqual(p.exitcode, code)

   def testSysEeprom(self):
      self._runMain(['syseeprom'])

   def testPlatforms(self):
      self._runMain(['platforms'])

   def _foreachPlatform(self, *args, **kwargs):
      code = kwargs.get('code', 0)
      loadPlatforms()
      for platform in getPlatforms():
         key = platform.SID[0] if platform.SID else platform.SKU[0]
         args = ['-p', key, '-s'] + list(args)
         self._runMain(args, code)

   def testSetup(self):
      self._foreachPlatform('setup')

   def testSetupBackground(self):
      self._foreachPlatform('setup', '--reset', '--background')

   @patch('time.sleep', return_value=None)
   def testResetToggle(self, patched_time):
      self._foreachPlatform('reset', '--toggle')

   def testClean(self):
      self._foreachPlatform('clean')

   def testDump(self):
      self._foreachPlatform('dump')

   def testRebootCause(self):
      self._foreachPlatform('reboot-cause')

   def testDiag(self):
      self._foreachPlatform('diag')

   def testWatchdogStatus(self):
      self._foreachPlatform('watchdog', '--status')

   def testWatchdogArm(self):
      self._foreachPlatform('watchdog', '--arm')

   def testWatchdogArmTimeout(self):
      self._foreachPlatform('watchdog', '--arm', '500')

   def testWatchdogStop(self):
      self._foreachPlatform('watchdog', '--stop')

if __name__ == '__main__':
   unittest.main()
