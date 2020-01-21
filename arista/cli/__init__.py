#!/usr/bin/env python

from __future__ import print_function, with_statement

import logging
import logging.handlers
import argparse
import tempfile
import time
import sys
import os

from .args import getParsers
from .actions import getAction

from .. import platforms

from ..core import utils
from ..core.config import Config
from ..core.platform import getPlatform

def checkRootPermissions():
   if utils.inSimulation():
      return

   if os.geteuid() != 0:
      logging.error('You must be root to use this feature')
      sys.exit(1)

def setupLogging(verbose=False, logfile=None, syslog=False):
   loglevel = logging.DEBUG if verbose else logging.INFO
   dateFmt = '%Y-%m-%d %H:%M:%S'

   log = logging.getLogger()
   log.setLevel(logging.DEBUG)

   logOut = logging.StreamHandler(sys.stdout)
   logOut.setFormatter(logging.Formatter('%(levelname)s: %(message)s'))
   logOut.setLevel(loglevel)
   log.addHandler(logOut)

   if logfile:
      logFile = logging.FileHandler(logfile)
      logFile.setFormatter(logging.Formatter(
            '%(asctime)s.%(msecs)03d %(levelname)s: %(message)s', datefmt=dateFmt))
      log.addHandler(logFile)

   if syslog:
      logSys = logging.handlers.SysLogHandler()
      # format to rfc5424 format
      logSys.setFormatter(
            logging.Formatter('{} arista: %(message)s'.format(utils.getHostname())))
      logSys.setLevel(logging.WARNING)
      log.addHandler(logSys)
      try:
         # the connection to the syslog socket happens with the first message
         log.info('Attaching to syslog')
      except:
         log.warning('Failed open syslog')

def setupSimulation():
   utils.simulation = True
   assert utils.inSimulation()

   logging.info('Running in simulation mode')
   Config().lock_file = tempfile.mktemp(prefix='arista-', suffix='.lock')

def addCommonArgs(parser):
   parser.add_argument('-v', '--verbose', action='store_true',
                       help='increase verbosity')

def parseArgs(args):
   parser = argparse.ArgumentParser(
      description='Arista platform management framework',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter
   )
   parser.add_argument('-p', '--platform', type=str,
                       help='name of the platform to load')
   parser.add_argument('-l', '--logfile', type=str,
                       help='log file to log to')
   parser.add_argument('-s', '--simulation', action='store_true',
                       help='force simulation mode')
   parser.add_argument('--syslog', action='store_true',
                       help='also send logs to syslog' )
   addCommonArgs(parser)

   subparsers = parser.add_subparsers(dest='action')
   subparsers.add_parser('help', help='print a help message')
   for subparser in getParsers():
      sub = subparsers.add_parser(
         subparser.name,
         formatter_class=argparse.RawDescriptionHelpFormatter,
         **subparser.kwargs
      )
      addCommonArgs(sub)
      subparser.func(sub)

   args = parser.parse_args(args)
   if args.action is None or args.action == 'help':
      parser.print_help()
      sys.exit(0)
   return args

def runAction(args):
   action = getAction(args.action)
   if action is None:
      logging.error("Command %s doesn't exists", args.action)
      return 1

   platform = None
   if action.needsPlatform:
      checkRootPermissions()
      platform = getPlatform(args.platform)

   ret = action.func(args, platform)
   if ret is None or ret == 0:
      return 0
   return int(ret)

def main(args):
   args = parseArgs(args)

   setupLogging(args.verbose, args.logfile, args.syslog)

   if args.simulation:
      setupSimulation()

   logging.debug(args)

   return runAction(args)

