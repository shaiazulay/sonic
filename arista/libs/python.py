
import sys

if sys.version_info.major == 2:
   def isinteger(value):
      return isinstance(value, (int, long))
else:
   def isinteger(value):
      return isinstance(value, int)
