from __future__ import absolute_import, division, print_function

class DiagContext(object):
   def __init__(self, performIo=True, recursive=False):
      self.performIo = performIo
      self.recursive = recursive
