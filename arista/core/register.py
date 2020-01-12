
from __future__ import absolute_import, division, print_function

import logging

class HardwareHandle(object):

   def __str__(self):
      raise NotImplementedError

   def read(self):
      raise NotImplementedError

   def write(self, value):
      raise NotImplementedError

class RegBitField(HardwareHandle):
   def __init__(self, bitpos, name, ro=True, flip=False, parent=None):
      '''Parent of this class is Register'''
      self.parent = parent
      self.bitpos = bitpos
      self.name = name
      self.ro = ro
      self.flip = flip

   def __str__(self):
      return '%s Bit(%d, %s, ro=%s)' % (self.parent, self.bitpos, self.name, self.ro)

   def read(self):
      value = self.parent.readBit(self.bitpos)
      if self.flip:
         value = not value
      return value

   def write(self, value):
      assert not self.ro
      if self.flip:
         value = not value
      return self.parent.writeBit(self.bitpos, value)

   def readWrite(self, value=None):
      if value is None:
         return self.read()
      return self.write(value)

   def getAttribute(self, parent=None):
      self.parent = parent
      return self.readWrite

class Register(HardwareHandle):
   def __init__(self, addr, *fields, **kwargs):
      self.parent = kwargs.get('parent')
      self.addr = addr
      self.fields = fields
      self.name = kwargs.get('name')
      self.ro = kwargs.get('ro')

   def __str__(self):
      return 'Register(%s, %s)' % (self.addr, self.name)

   def split(self):
      pass

   def dump(self):
      return {}

   def read(self):
      return self.parent.read(self.addr)

   def write(self, value):
      return self.parent.write(self.addr, value)

   def readWrite(self, value=None):
      if value is None:
         return self.read()
      return self.write(value)

   def readBit(self, bitpos):
      return (self.read() >> bitpos) & 1

   def writeBit(self, bitpos, value):
      regval = self.read()
      if value:
         regval |= (1 << bitpos)
      else:
         regval &= ~(1 << bitpos)
      return self.write(regval)

   def generateAttributes(self, parent=None):
      if parent is not None:
         self.parent = parent
      assert self.parent is not None

      attrs = {}
      if self.name:
         attrs[self.name] = self.readWrite
      for field in self.fields:
         if hasattr(field, 'getAttribute'):
            attrs[field.name] = field.getAttribute(self)

      return attrs

class RegisterMap(object):
   def __init__(self, parent):
      self.parent_ = parent
      self.attributes_ = []
      for key in dir(self):
         attr = getattr(self, key)
         if isinstance(attr, Register):
            self._updateAttributes(attr)

   def _updateAttributes(self, reg):
      attrs = reg.generateAttributes(self.parent_)
      for key, value in attrs.items():
         logging.debug('registering reg: %s', key)
         self.attributes_.append(key)
         setattr(self, key, value)

   def __diag__(self, ctx):
      res = []
      for attr in self.attributes_:
         func = getattr(self, attr)
         try:
            value = func() if ctx.performIo else None
         except IOError:
            value = False
         info = {
            'name': str(attr),
            'addr': str(func.__self__),
            'value': value
         }

         res.append(info)
      return res


