# Copyright (c) 2017 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

from __future__ import print_function

import subprocess

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

def ceosManagesXcvrs():
   return getSonicVersVar('asic_type') == 'ceos'

def ceosManagesLeds():
   return getSonicVersVar('asic_type') == 'ceos'

