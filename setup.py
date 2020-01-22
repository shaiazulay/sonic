#!/usr/bin/env python

from setuptools import setup, find_packages
import os

setup(
   name='platform-arista',
   version='%s' % os.environ.get('ARISTA_PLATFORM_MODULE_VERSION', '1.0'),
   description='Module to initialize arista platforms',
   install_requires=['pyyaml'],
   packages=find_packages(exclude=["*.tests", "*.tests.*", "tests.*", "tests"]),
   test_suite='tests',
)
