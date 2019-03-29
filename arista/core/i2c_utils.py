from ctypes import c_uint8, c_uint16, c_uint32, cast, pointer, POINTER
from ctypes import create_string_buffer, Structure
from fcntl import ioctl

I2C_M_RD = 0x0001
I2C_RDWR = 0x0707

class i2c_msg(Structure):
   _fields_ = [
      ('addr', c_uint16),
      ('flags', c_uint16),
      ('len', c_uint16),
      ('buf', POINTER(c_uint8))
   ]

class i2c_rdwr_ioctl_data(Structure):
   _fields_ = [
      ('msgs', POINTER(i2c_msg)),
      ('nmsgs', c_uint32)
   ]

def _makeI2cRdwrRequest(addr, reg, size, data, read):
   msg_data_type = i2c_msg*2
   msg_data = msg_data_type()
   msg_data[0].addr = addr
   msg_data[0].flags = 0
   msg_data[0].len = 1
   msg_data[0].buf = reg
   msg_data[1].addr = addr
   msg_data[1].flags = I2C_M_RD if read else 0
   msg_data[1].len = size
   msg_data[1].buf = data
   request = i2c_rdwr_ioctl_data()
   request.msgs = msg_data
   request.nmsgs = 2
   return request

class I2cMsg(object):
   def __init__(self, addr):
      self.addr = addr
      self.device = None

   def __str__(self):
      return '%s(addr=%s, device=%s)' % (self.__class__.__name__, self.addr, self.device)

   def open(self):
      if self.device is None:
         self.device = open("/dev/i2c-%d" % self.addr.bus, 'r+b', buffering=0)

   def close(self):
      if self.device:
         self.device.close()
         self.device = None

   def __enter__(self):
      self.open()
      return self

   def __exit__(self, *args):
      self.close()

   def setI2cBlock(self, devAddr, command, data):
      length = len(data)
      result = create_string_buffer(length)
      for i in range(0, length):
         cast(result, POINTER(c_uint8))[i] = data[i]
      reg = c_uint8(command)
      request = _makeI2cRdwrRequest(devAddr, pointer(reg), length,
                                    cast(result, POINTER(c_uint8)), 0)
      ioctl(self.device.fileno(), I2C_RDWR, request)

   def getI2cBlock(self, devAddr, command, length):
      result = create_string_buffer(length)
      reg = c_uint8(command)
      request = _makeI2cRdwrRequest(devAddr, pointer(reg), length,
                                    cast(result, POINTER(c_uint8)), 1)
      ioctl(self.device.fileno(), I2C_RDWR, request)
      return [ord(c) for c in result.raw]
