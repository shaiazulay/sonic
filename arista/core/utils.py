import logging
import mmap
import fcntl
import os

from struct import pack, unpack
from functools import wraps

class MmapResource(object):
   """Resource implementation for a directly-mapped memory region."""
   def __init__(self, path):
      self.path = path
      self.mmap_ = None

   def map(self):
      try:
         fd = os.open(self.path, os.O_RDWR)
      except EnvironmentError:
         logging.error("FAIL can not open scd memory-map resource file")
         logging.error("FAIL are you running on the proper platform?")
         return False

      try:
         size = os.fstat(fd).st_size
      except EnvironmentError:
         logging.error("FAIL can not fstat scd memory-map resource file")
         logging.error("FAIL are you running on the proper platform?")
         return False

      try:
         self.mmap_ = mmap.mmap(fd, size, mmap.MAP_SHARED,
                                mmap.PROT_READ | mmap.PROT_WRITE)
      except EnvironmentError:
         logging.error("FAIL can not map scd memory-map file")
         logging.error("FAIL are you running on the proper platform?")
         return False
      finally:
         try:
            # Note that closing the file descriptor has no effect on the memory map
            os.close(fd)
         except EnvironmentError:
            logging.error("FAIL failed to close scd memory-map file")
            return False
      return True

   def close( self ):
      self.mmap_.close()

   def read32( self, addr ):
      return unpack( '<L', self.mmap_[ addr : addr + 4 ] )[ 0 ]

   def write32( self, addr, value ):
      self.mmap_[ addr: addr + 4 ] = pack( '<L', value )

def sysfsFmtHex(x):
   return "0x%08x" % x

def sysfsFmtDec(x):
   return "%d" % x

def sysfsFmtStr(x):
   return str(x)

def incrange(start, stop):
   return list(range(start, stop + 1))

def flatten(nestedList):
   return [val for sublist in nestedList for val in sublist]

def klog(msg, level=2, *args):
   try:
      with open('/dev/kmsg', 'w') as f:
         f.write('<%d>arista: %s\n' % (level, msg % tuple(*args)))
   except:
      pass

class FileLock:
   def __init__(self, lock_file):
      self.f = open(lock_file, 'w')

   def lock(self):
      fcntl.flock(self.f, fcntl.LOCK_EX)

   def unlock(self):
      fcntl.flock(self.f, fcntl.LOCK_UN)
      self.f.close()

   def __enter__(self):
      self.lock()

   def __exit__(self, exc_type, exc_val, traceback):
      self.unlock()

class NoopObj(object):
   def __init__(self, *args, **kwargs):
      self.name = self.__class__.__name__
      self.classStr = '%s(%s)' % (self.name, self._fmtArgs(*args, **kwargs))
      logging.debug(self.classStr)

   def _fmtArgs(self, *args, **kwargs):
      kw = ['%s=%s' % (k,v) for k, v in kwargs.items()]
      return ', '.join(list(map(str, args)) + kw)

   def noop(self, attr):
      def wrapped(*args, **kwargs):
         funcStr = '%s(%s)' % (attr, self._fmtArgs(*args, **kwargs))
         logging.debug('%s.%s', self.classStr, funcStr)
      return wrapped

   def __getattr__(self, attr):
      return self.noop(attr)

CMDLINE_PATH = '/proc/cmdline'

cmdlineDict = {}
def getCmdlineDict():
   global cmdlineDict

   if cmdlineDict:
      return cmdlineDict

   data = {}
   with open(CMDLINE_PATH) as f:
      for entry in f.read().split():
         idx = entry.find('=')
         if idx == -1:
            data[entry] = None
         else:
            data[entry[:idx]] = entry[idx+1:]

   cmdlineDict = data
   return data

# debug flag, if enabled should use the most tracing possible
debug = False

# force simulation to be True if not on a Arista box
simulation = True

# simulation related globals
SMBus = None

def inDebug():
   return debug

def inSimulation():
   return simulation

def simulateWith(simulatedFunc):
   def simulateThisFunc(func):
      @wraps(func)
      def funcWrapper(*args, **kwargs):
         if inSimulation():
            return simulatedFunc(*args, **kwargs)
         return func(*args, **kwargs)
      return funcWrapper
   return simulateThisFunc

def libraryInit():
   global simulation, debug, SMBus

   cmdline = getCmdlineDict()
   if "Aboot" in cmdline:
      simulation = False

   if "arista-debug" in cmdline:
      debug = True

   if simulation:
      SMBus = type('SMBus', (NoopObj,), {})
   else:
      try:
         from smbus import SMBus
      except ImportError:
         pass

libraryInit()

