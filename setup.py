#!/usr/bin/env python

from setuptools import setup
import os

setup(
   name='platform-arista',
   version='%s' % os.environ.get('ARISTA_PLATFORM_MODULE_VERSION', '1.0'),
   description='Module to initialize arista platforms',
   install_requires=['pyyaml'],
   packages=[
      'arista',
      'arista.accessors',
      'arista.cli',
      'arista.core',
      'arista.components',
      'arista.drivers',
      'arista.platforms',
      'arista.utils',
      'arista.utils.sonic_platform',
      'sonic_platform',
   ],
   test_suite='tests',
)
