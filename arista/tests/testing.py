
from __future__ import absolute_import, division, print_function

# pylint: disable=unused-import

import re
import unittest

try:
   import unittest.mock as mock
except ImportError:
   import mock

patch = mock.patch

# these methods only exist in modern versions of python
if not hasattr( unittest.TestCase, 'assertRegex' ):
   def assertRegex( self, string, regex, **kwargs ):
      self.assertIsNotNone( re.search( regex, string ), **kwargs )
   setattr( unittest.TestCase, 'assertRegex', assertRegex )

   def assertNotRegex( self, string, regex, **kwargs ):
      self.assertIsNone( re.search( regex, string ), **kwargs )
   setattr( unittest.TestCase, 'assertNotRegex', assertNotRegex )
