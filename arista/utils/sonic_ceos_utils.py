# Copyright (c) 2017 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from __future__ import print_function

import subprocess
import socket
import sys
try:
   import jsonrpclib
except:
   pass

from arista.utils.sonic_utils import getSonicVersVar


# only works on cEOS host
def runCliCmd(cmd):
   output = None
   fullCmd = ['docker', 'exec', 'ceos', 'Cli', '-c']
   fullCmd.extend(cmd)
   try:
      output = subprocess.check_output(fullCmd)
   except subprocess.CalledProcessError as e:
      print(e.output)

   return output

class CeosCli(object):
   def __init__(self):
      self.ceosCli = jsonrpclib.Server("http://localhost:8080/command-api)")

   def getCmdJson(self, cmd, attribute):
      try:
         response = self.ceosCli.runCmds(1, [cmd])
      except jsonrpclib.jsonrpc.ProtocolError as e:
         print(e.message, file=sys.stderr)
         return {}
      except socket.error as e:
         print(e, file=sys.stderr)
         return {}
      return response[0].get(attribute, {})

   def runCmds(self, cmdsList):
      try:
         self.ceosCli.runCmds(1, cmdsList)
      except jsonrpclib.jsonrpc.ProtocolError as e:
         print(e.message, file=sys.stderr)
      except socket.error as e:
         print(e, file=sys.stderr)

def ceosManagesXcvrs():
   return getSonicVersVar('asic_type') == 'ceos'

def ceosManagesLeds():
   return getSonicVersVar('asic_type') == 'ceos'

def ceosManagesPsus():
   return getSonicVersVar('asic_type') == 'ceos'

