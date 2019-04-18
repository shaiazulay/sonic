from __future__ import print_function

import logging
import subprocess
import os
import sys

from collections import OrderedDict, namedtuple, defaultdict

from .inventory import Inventory
from .component import Component, Priority
from .utils import simulateWith
from .driver import modprobe, rmmod, KernelDriver

from . import prefdl

platforms = {}
syseeprom = None

host_prefdl_path = '/host/.system-prefdl'
host_prefdl_path_bin = '/host/.system-prefdl-bin'
fmted_prefdl_path = '/etc/sonic/.syseeprom'

def formatPrefdlData(data):
   formatDict = {
      "MAC": ["MAC", "MacAddrBase", "Mac"],
      "SKU": ["SKU", "Sku"],
      "SerialNumber": ["SerialNumber"],
   }
   fdata = { }
   for k, v in data.items():
      for kfmt, vfmt in formatDict.items():
         if k in vfmt:
            if kfmt == "MAC":
               val = prefdl.showMac(v)
            else:
               val = v
            fdata[kfmt] = val
   return fdata

def writeFormattedPrefdl(pfdl, f):
   fdata = formatPrefdlData(pfdl.data())
   with open(f, 'w+', 0) as fp:
      for k, v in fdata.items():
         fp.write("%s: %s\n" % (k, v))

def readPrefdl():
   if os.path.isfile(fmted_prefdl_path) and \
      os.path.getsize(fmted_prefdl_path) > 0:
      with open(fmted_prefdl_path) as fp:
         logging.debug('reading system eeprom from %s', fmted_prefdl_path)
         return prefdl.PreFdlFromFile(fp)

   if os.path.exists(host_prefdl_path_bin):
      with open(host_prefdl_path_bin) as fp:
         logging.debug('reading bin system eeprom from %s',
                       host_prefdl_path_bin)
         pfdl = prefdl.decode(fp)
         writeFormattedPrefdl(pfdl, fmted_prefdl_path)
         return pfdl

   if os.path.exists(host_prefdl_path):
      with open(host_prefdl_path) as fp:
         logging.debug('reading system eeprom from %s', host_prefdl_path)
         pfdl = prefdl.PreFdlFromFile(fp)
      writeFormattedPrefdl(pfdl, fmted_prefdl_path)
      with open(fmted_prefdl_path) as fp:
         return prefdl.PreFdlFromFile(fp)

   modprobe('eeprom')
   for addr in ['1-0052']:
      eeprompath = os.path.join('/sys/bus/i2c/drivers/eeprom', addr, 'eeprom')
      if not os.path.exists(eeprompath):
         continue
      try:
         with open(eeprompath) as fp:
            logging.debug('reading system eeprom from %s', eeprompath)
            pfdl = prefdl.decode(fp)
            pfdl.writeToFile(fmted_prefdl_path)
            return pfdl
      except Exception as e:
         logging.warn('could not obtain prefdl from %s', eeprompath)
         logging.warn('error seen: %s', e)
   raise RuntimeError("Could not find valid system eeprom")

def getPrefdlDataSim():
   logging.debug('bypass prefdl reading by returning default values')
   return {'SKU': 'simulation'}

@simulateWith(getPrefdlDataSim)
def getPrefdlData():
   return readPrefdl().data()

def getSysEeprom():
   global syseeprom
   if not syseeprom:
      syseeprom = getPrefdlData()
      assert 'SKU' in syseeprom
   return syseeprom

def detectPlatform():
   return getSysEeprom()['SKU']

def getPlatform(name=None):
   if name is None:
      name = detectPlatform()
   platform = platforms[name]()
   platform.refresh()
   return platform

def getPlatforms():
   return platforms

def registerPlatform(skus):
   global platforms
   def wrapper(cls):
      if isinstance(skus, list):
         for sku in skus:
            platforms[sku] = cls
      else:
         platforms[skus] = cls
      return cls
   return wrapper

class Platform(Component):
   def __init__(self, drivers=None, **kwargs):
      drivers = drivers or [KernelDriver(module='eeprom'),
                            KernelDriver(module='i2c-dev')]
      super(Platform, self).__init__(drivers=drivers, **kwargs)
      self.inventory = Inventory()

   def setup(self, priority=Priority.DEFAULT):
      super(Platform, self).setup()
      super(Platform, self).finish(priority)

   def getInventory(self):
      return self.inventory

   def __str__(self):
      return '%s()' % self.__class__.__name__
