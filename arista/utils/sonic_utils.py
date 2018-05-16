import os
import re
import subprocess
from collections import namedtuple

from ..core.utils import runningInContainer

Port = namedtuple('Port', ['portNum', 'lanes', 'offset', 'singular'])

def parsePortConfig():
   '''
   Returns a dictionary mapping port name ("Ethernet48") to a named tuple of port
   number, # of lanes, the offset (0 to 3 from the first lane in qsfp) and the
   singularity of the lane (if it is in 100G/40G mode)
   '''
   portMapping = {}

   with open(portConfigPath()) as fp:
      for line in fp:
         line = line.strip()
         if not line or line[0] == '#':
            continue

         fields = line.split()
         # "portNum" is determined from the fourth column (port), or the first number
         # in the third column (alias).
         # "lanes" is determined from the number of lanes in the second column.
         # "offset" is determined from the second number in the third column (alias).
         # "singular" is determined by if the alias has a '/' character or not.
         if len(fields) < 3:
            continue
         name = fields[0]
         lanes = len(fields[1].split(','))
         alias = fields[2]
         aliasRe = re.findall(r'\d+', alias)
         try:
            portNum = int(fields[3])
         except IndexError:
            portNum = int(aliasRe[0])
         if len(aliasRe) < 2:
            offset = 0
            singular = True
         else:
            offset = int(aliasRe[1]) - 1
            singular = False

         portMapping[name] = Port(portNum, lanes, offset, singular)

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
