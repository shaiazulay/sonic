# Copyright (c) 2017 Arista Networks, Inc.  All rights reserved.
# Arista Networks, Inc. Confidential and Proprietary.

import subprocess
from arista.utils.sonic_utils import parsePortConfig

# only works on host
def runCliCmd(cmd):
   fullCmd = ['docker', 'exec', 'ceos', 'Cli', '-c']
   fullCmd.extend( cmd )
   return subprocess.check_output(fullCmd)

