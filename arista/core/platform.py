from __future__ import print_function

import logging
import os

from .exception import UnknownPlatformError
from .fixed import FixedSystem
from .utils import simulateWith, getCmdlineDict
from .driver import modprobe

from . import prefdl

platforms = []
platformSidIndex = {}
platformSkuIndex = {}
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

def readPrefdlEeprom(*addrs):
   for addr in addrs:
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
   return readPrefdlEeprom('1-0052')

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

def readSku():
   return getSysEeprom().get('SKU')

def readSid():
   return getCmdlineDict().get('sid')

def readPlatformName():
   return getCmdlineDict().get('platform')

def detectPlatform():
   sid = readSid()
   platformCls = platformSidIndex.get(sid)
   if platformCls is not None:
      return platformCls

   sku = readSku()
   platformCls = platformSkuIndex.get(sku)
   if platformCls is not None:
      return platformCls

   name = readPlatformName()
   platformCls = platformSidIndex.get(name)
   if platformCls is not None:
      return platformCls

   raise UnknownPlatformError(sku, sid, name, platforms)

def getPlatform(name=None):
   if name is None:
      platformCls = detectPlatform()
   else:
      platformCls = platformSkuIndex.get(name)
      if platformCls is None:
         platformCls = platformSidIndex.get(name)
         if platformCls is None:
            raise UnknownPlatformError(name, platforms)

   platform = platformCls()
   platform.refresh()
   return platform

def getPlatformSkus():
   return platformSkuIndex

def getPlatformSids():
   return platformSidIndex

def getPlatforms():
   return platforms

def loadPlatforms():
   logging.debug('Loading platform definitions')
   from .. import platforms as _unused
   logging.debug('Loaded %d platforms', len(platforms))

def registerPlatform(skus=None):
   def wrapper(cls):
      platforms.append(cls)

      if cls.SID is not None:
         for sid in cls.SID:
            platformSidIndex[sid] = cls
      if cls.SKU is not None:
         for sku in cls.SKU:
            platformSkuIndex[sku] = cls

      if cls.PLATFORM is not None:
         # this is a hack for older platforms that did not provide sid=
         assert cls.PLATFORM not in platformSidIndex
         platformSidIndex[cls.PLATFORM] = cls

      # legacy code to be removed
      if skus is not None:
         for sku in skus:
            platformSkuIndex[sku] = cls

      return cls
   return wrapper

# XXX: This is here for legacy reasons
Platform = FixedSystem
