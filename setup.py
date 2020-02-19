#!/usr/bin/env python

import fnmatch
import os
import sys

from setuptools import setup, find_packages
from setuptools.command.build_py import build_py

package_exclude = [
   "*.tests",
   "*.tests.*",
   "tests.*",
   "tests",
]
file_exclude = []

if sys.version_info.major == 2:
   # these sources are python3 only, they raise SyntaxError on python2
   package_exclude.extend([
      '*.daemon',
      '*.daemon.*',
   ])
   file_exclude.extend([
      '*/daemon.py',
   ])

class build_py_with_exclude(build_py):
   def find_package_modules(self, package, package_dir):
      modules = build_py.find_package_modules(self, package, package_dir)
      return [
         (pkg, mod, f)
         for (pkg, mod, f) in modules
         if not any(fnmatch.fnmatchcase(f, pat=pattern) for pattern in file_exclude)
      ]

setup(
   name='platform-arista',
   version='%s' % os.environ.get('ARISTA_PLATFORM_MODULE_VERSION', '1.0'),
   description='Module to initialize arista platforms',
   install_requires=['pyyaml'],
   packages=find_packages(exclude=package_exclude),
   test_suite='tests',
   cmdclass={'build_py': build_py_with_exclude},
)
