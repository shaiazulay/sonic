import os

from collections import namedtuple

Register = namedtuple("Register", ["addr", "ro"])
NamedRegister = namedtuple("NamedRegister", Register._fields + ("name", ))

Gpio = namedtuple("Gpio", ["bit", "ro", "activeLow"])
NamedGpio = namedtuple("NamedGpio", ("addr",) + Gpio._fields + ("name",))

ResetGpio = namedtuple("ResetGpio", ["addr", "bit", "activeLow", "name"])

class SysfsPath(object):
   def getSysfsPath(self):
      raise NotImplementedError

class I2cAddr(SysfsPath):
   def __init__(self, bus, address):
      self.bus_ = bus
      self.address_ = address

   @property
   def bus(self):
      return self.bus_

   @property
   def address(self):
      return self.address_

   def __str__(self):
      return '%d-00%02x' % (self.bus, self.address)

   def getSysfsPath(self):
      return os.path.join('/sys/bus/i2c/devices', str(self))

class PciAddr(SysfsPath):
   def __init__(self, domain=0, bus=0, device=0, func=0):
      self.domain = domain
      self.bus = bus
      self.device = device
      self.func = func

   def __str__(self):
      return '%04x:%02x:%02x.%d' % (self.domain, self.bus, self.device, self.func)

   def getSysfsPath(self):
      return os.path.join('/sys/bus/pci/devices', str(self))

class MdioClause:
   C22 = 1
   C45 = 2

class MdioSpeed:
   S20 = 0
   S2_5 = 1
   S5 = 2
   S10 = 3
