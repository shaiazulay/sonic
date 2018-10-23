import os
import re
import subprocess
from collections import namedtuple

from ..core.utils import runningInContainer

Port = namedtuple('Port', ['portNum', 'lanes', 'singular', 'alias'])

def parsePortConfig():
   '''
   Returns a dictionary mapping port name ("Ethernet48") to a named tuple of port
   number, # of lanes, and the
   singularity of the lane (if it is in 100G/40G mode)
   '''
   portMapping = {}

   with open(portConfigPath()) as fp:
      header = fp.readline()[1:].split()
      headerMap = {key.strip(): idx for (idx, key) in enumerate(header)}
      for line in fp:
         line = line.strip()
         if not line or line[0] == '#':
            continue

         fields = line.split()
         # "portNum" is determined from the "index" column or derived from the
         # "alias" column.
         # "lanes" is determined from the number of lanes in the "lanes" column.
         # "singular" is determined by if the alias has a '/' character or not.
         name = fields[headerMap['name']]
         lanes = len(fields[headerMap['lanes']].split(','))
         alias = fields[headerMap['alias']]
         aliasRe = re.findall(r'\d+', alias)
         portNum = int(fields[headerMap['index']]) if headerMap.get('index') else \
                   int(aliasRe[0])
         if len(aliasRe) < 2:
            singular = True
         else:
            singular = False

         portMapping[name] = Port(portNum, lanes, singular, alias)

   return portMapping

def getSonicConfigVar(name):
   return subprocess.check_output(['sonic-cfggen', '-d', '-v',
                                   name.replace('"', "'")]).strip()

def getSonicPlatformName():
   platformKey = "DEVICE_METADATA['localhost']['platform']"
   return getSonicConfigVar(platformKey)

def getSonicHwSkuName():
   hwSkuKey = "DEVICE_METADATA['localhost']['hwsku']"
   return getSonicConfigVar(hwSkuKey)

def portConfigPath():
   CONTAINER_PORT_CONFIG_PATH = "/usr/share/sonic/hwsku/port_config.ini"
   if runningInContainer():
      return CONTAINER_PORT_CONFIG_PATH
   hwSku = getSonicHwSkuName()
   platform = getSonicPlatformName()
   return os.path.join("/usr/share/sonic/device", platform, hwSku,
                        "port_config.ini")
