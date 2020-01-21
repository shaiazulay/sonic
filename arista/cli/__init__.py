#!/usr/bin/env python

from __future__ import print_function, with_statement

import argparse
import tempfile
import time
import sys
import os

from .parser import CliContext, ActionError
from .args import getRootParser, registerParser
from .actions import registerAction

from .. import platforms

from ..core import utils
from ..core.config import Config
from ..core.backtrace import loadBacktraceHook
from ..core.log import setupLogging, getLogger

logging = getLogger(__name__)

def setupSimulation():
   utils.simulation = True
   assert utils.inSimulation()

   logging.info('Running in simulation mode')
   Config().lock_file = tempfile.mktemp(prefix='arista-', suffix='.lock')

def addCommonArgs(parser):
   parser.add_argument('-v', '--verbosity', type=str,
                       help='set verbosity')

def rootParser(parser):
   parser.add_argument('-p', '--platform', type=str,
                       help='name of the platform to load')
   parser.add_argument('-l', '--logfile', type=str,
                       help='log file to log to')
   parser.add_argument('-s', '--simulation', action='store_true',
                       help='force simulation mode')
   parser.add_argument('--syslog', action='store_true',
                       help='also send logs to syslog')
   addCommonArgs(parser)

def parseArgs(args):
   parser = argparse.ArgumentParser(
      description='Arista platform management framework',
      formatter_class=argparse.ArgumentDefaultsHelpFormatter
   )

   rootParser(parser)

   root = getRootParser()
   root.addSubparsers(parser, common=addCommonArgs)

   args = parser.parse_args(args)
   if args.action is None or args.action == 'help':
      parser.print_help()
      sys.exit(0)

   return root, args

def main(args):
   root, args = parseArgs(args)

   try:
      setupLogging(args.verbosity, args.logfile, args.syslog)
   except LoggerError as e:
      print(e.msg)
      return e.code

   if args.verbosity:
      loadBacktraceHook()

   if args.simulation:
      setupSimulation()

   logging.debug(args)

   try:
      root.runAction(CliContext(), args)
   except ActionError as e:
      logging.error('%s', e)
      return e.code

   return 0
