import os.path

from ..inventory.gpio import Gpio

class GpioImpl(Gpio):
   def __init__(self, path, name, addr, bit, ro=False, activeLow=False, **kwargs):
      self.name = name
      self.addr = addr
      self.bit = bit
      self.ro = ro
      self.activeLow = activeLow
      self.path = os.path.join(path, name)
      self.__dict__.update(kwargs)

   def getName(self):
      return self.name

   def getAddr(self):
      return self.addr

   def getPath(self):
      return self.path

   def getBit(self):
      return self.bit

   def isRo(self):
      return self.ro

   def isActiveLow(self):
      return self.activeLow

   def getRawValue(self):
      with open(self.path, 'r') as f:
         return int(f.read())

   def _activeValue(self):
      return 0 if self.isActiveLow() else 1

   def isActive(self):
      return self.getRawValue() == self._activeValue()

   def setActive(self, value):
      if self.isActiveLow():
         value = not value

      with open(self.path, 'w') as f:
         f.write(int(value))
