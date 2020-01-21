
from __future__ import absolute_import, division, print_function

class ActionError(Exception):
   def __init__(self, msg, code=1):
      self.code = code
      self.msg = msg

   def __str__(self):
      return 'ActionError: %s (code %d)' % (self.msg, self.code)

