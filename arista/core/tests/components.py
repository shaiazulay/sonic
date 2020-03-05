
from __future__ import absolute_import, division, print_function

from ...tests.testing import unittest, patch
from ...core import component
from ...core.component import Component
from ...core.fixed import FixedSystem
from ...core.platform import loadPlatforms, getPlatforms

class ComponentTest(unittest.TestCase):
   def testSetup(self):
      loadPlatforms()
      for platformCls in getPlatforms():
         if not issubclass(platformCls, FixedSystem):
            continue
         platform = platformCls()

         mocks = []
         for c in platform.iterComponents():
            mocks.append(patch.object(c, 'setup').start())

         platform.setup()

         for mock in mocks:
            mock.assert_called_once()

if __name__ == '__main__':
   unittest.main()
