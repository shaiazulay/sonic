from __future__ import print_function

import logging
import os
import subprocess

from collections import OrderedDict

from .types import I2cAddr
from .utils import FileWaiter, inDebug, inSimulation

def modprobe(name, args=None):
   logging.debug('loading module %s', name)
   if args is None:
      args = []
   args = ['modprobe', name.replace('-', '_')] + args
   if inDebug():
      args += [ 'dyndbg=+pf' ]
   if inSimulation():
      logging.debug('exec: %s', ' '.join(args))
   else:
      subprocess.check_call(args)

def rmmod(name):
   logging.debug('unloading module %s', name)
   args = ['modprobe', '-r', name.replace('-', '_')]
   if inSimulation():
      logging.debug('exec: %s', ' '.join(args))
   else:
      subprocess.check_call(args)

def isModuleLoaded(name):
   with open('/proc/modules') as f:
      start = '%s ' % name.replace('-', '_')
      for line in f.readlines():
         if line.startswith(start):
            return True
   return False

_i2cBuses = OrderedDict()
def getKernelI2cBuses(force=False):
   if _i2cBuses and not force:
      return _i2cBuses
   _i2cBuses.clear()
   buses = {}
   root = '/sys/class/i2c-adapter'
   for busName in sorted(os.listdir(root), key=lambda x: int(x[4:])):
      busId = int(busName.replace('i2c-', ''))
      with open(os.path.join(root, busName, 'name')) as f:
         buses[busId] = f.read().rstrip()
   return buses

def i2cBusFromName(name, idx=0, force=False):
   buses = getKernelI2cBuses(force=force)
   for busId, busName in buses.items():
      if name == busName:
         if idx > 0:
            idx -= 1
         else:
            return busId
   return None

class Driver(object):
   def __init__(self, **kwargs):
      self.__dict__.update(kwargs)

   def setup(self):
      pass

   def finish(self):
      pass

   def clean(self):
      pass

   def refresh(self):
      pass

   def resetIn(self):
      pass

   def resetOut(self):
      pass

   def getReloadCauses(self, clear=False):
      return []

   def dump(self, depth=0, prefix=' - '):
      spacer = ' ' * (depth * 3)
      print('%s%s%s' % (spacer, prefix, self))

class KernelDriver(Driver):
   # TODO: handle multiple kernel modules
   def __init__(self, module, waitFile=None, waitTimeout=None, args=None):
      self.module = module
      self.driverName = module
      self.args = args if args is not None else []
      self.fileWaiter = FileWaiter(waitFile, waitTimeout)

   def setup(self):
      modprobe(self.module, self.args)
      self.fileWaiter.waitFileReady()

   def clean(self):
      if self.loaded():
         try:
            rmmod(self.module)
         except Exception as e:
            logging.error('Failed to unload %s: %s', self.module, e)
      else:
         logging.debug('Module %s is not loaded', self.module)

   def loaded(self):
      return isModuleLoaded(self.module)

   def __str__(self):
      return '%s(%s)' % (self.__class__.__name__, self.module)
