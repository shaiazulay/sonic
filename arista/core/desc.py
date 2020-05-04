
from __future__ import absolute_import, division, print_function

class HwDesc(object):
   def __init__(self, **kwargs):
      for key, value in kwargs.items():
         setattr(self, key, value)

   def __diag__(self, ctx):
      return { k : v for k, v in self.__dict__.items() }
