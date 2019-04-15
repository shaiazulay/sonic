#!/usr/bin/env python
from __future__ import absolute_import

try:
   from mock import patch
except ImportError:
   from unittest.mock import patch
import unittest

from arista.components.ds460 import Ds460
from arista.components.scd import ScdInterruptRegister

from arista.core.driver import Driver
from arista.core.inventory import Psu, Xcvr
from arista.core.platform import getPlatforms
from arista.core.types import I2cAddr
import arista.core.utils

from arista.drivers.accessors import FanImpl, PsuImpl, XcvrImpl
from arista.drivers.i2c import I2cFanDriver
from arista.drivers.scd import ScdKernelDriver
from arista.drivers.sysfs import SysfsDriver

import arista.platforms

from tests.common import getLogger

# TODO: remove this type of simulation testing
def mock_inSimulation():
   return False

def mock_writeComponents(self, components, filename):
   assert components
   assert filename

def mock_read(self, name):
   assert name
   return '1'

def mock_write(self, name, value):
   assert name
   assert value != None

def mock_getStatus(self):
   return True

def mock_waitReady(self):
   return True

def mock_setup(self):
   return

def mock_finish(self):
   return

def mock_readReg(self, reg):
   assert reg
   return None

@patch('arista.core.utils.inSimulation', mock_inSimulation)
@patch.object(Ds460, 'getStatus', mock_getStatus)
@patch.object(ScdInterruptRegister, 'setup', mock_setup)
@patch.object(ScdInterruptRegister, 'readReg', mock_readReg)
@patch.object(ScdKernelDriver, 'finish', mock_finish)
@patch.object(ScdKernelDriver, 'waitReady', mock_waitReady)
@patch.object(ScdKernelDriver, 'writeComponents', mock_writeComponents)
@patch.object(SysfsDriver, 'read', mock_read)
@patch.object(SysfsDriver, 'write', mock_write)
@patch.object(I2cFanDriver, 'read', mock_read)
@patch.object(I2cFanDriver, 'write', mock_write)
@patch.object(I2cFanDriver, 'finish', mock_finish)
class MockTest(unittest.TestCase):
   @classmethod
   def setUpClass(cls):
      cls.logger = getLogger(cls.__name__)
      cls.inventories = {}
      for name, platform in getPlatforms().items():
         assert platform
         cls.logger.info('Testing init for platform %s', name)
         platformObj = platform()
         assert platformObj
         cls.logger.info('Setting inventory for platform %s', name)
         inventory = platformObj.getInventory()
         assert inventory
         cls.inventories[name] = inventory

   def testSetup(self):
      for name, platform in getPlatforms().items():
         self.logger.info('Testing setup for platform %s', name)
         platform = platform()
         platform.setup()

   def testXcvrs(self):
      for name, inventory in self.inventories.items():
         self.logger.info('Testing transceivers for platform %s', name)
         for index, xcvr in inventory.getXcvrs().items():
            self.logger.debug('Testing xcvr index %s', index)
            assert isinstance(xcvr, XcvrImpl)
            assert isinstance(xcvr.name, str)
            assert isinstance(xcvr.driver, Driver)
            assert isinstance(xcvr.addr, I2cAddr)
            assert xcvr.xcvrType in [Xcvr.SFP, Xcvr.QSFP, Xcvr.OSFP]
            assert isinstance(xcvr.xcvrId, int)
            assert isinstance(xcvr.getPresence(), bool)
            assert isinstance(xcvr.getLowPowerMode(), bool)
            xcvr.setLowPowerMode(0)
            xcvr.setLowPowerMode(1)
            assert isinstance(xcvr.getModuleSelect(), bool)
            xcvr.setModuleSelect(0)
            xcvr.setModuleSelect(1)
            assert isinstance(xcvr.getTxDisable(), bool)
            xcvr.setTxDisable(0)
            xcvr.setTxDisable(1)
            interruptLine = xcvr.getInterruptLine()
            assert interruptLine is xcvr.interruptLine
            if interruptLine:
               assert isinstance(interruptLine.reg, object)
               assert isinstance(interruptLine.bit, int)
               interruptLine.set()
               interruptLine.clear()
            reset = xcvr.getReset()
            assert reset is xcvr.reset
            if reset:
               assert isinstance(reset.name, str)
               assert isinstance(reset.driver, Driver)
               assert isinstance(reset.getName(), str)
               assert reset.read() in ['0', '1']
               reset.resetIn()
               reset.resetOut()

   def testPsus(self):
      for name, inventory in self.inventories.items():
         self.logger.info('Testing PSUs for platform %s', name)
         for psu in inventory.getPsus():
            assert isinstance(psu, Psu)
            # Need to resolve UpperlakePsu, which is not PsuImpl
            if isinstance(psu, PsuImpl):
               assert isinstance(psu.driver, Driver)
               assert isinstance(psu.psuId, int)
               assert isinstance(psu.getPresence(), bool)
               assert isinstance(psu.getStatus(), bool)

   def testFans(self):
      for name, inventory in self.inventories.items():
         self.logger.info('Testing fans for platform %s', name)
         for fan in inventory.getFans():
            assert isinstance(fan, FanImpl)
            assert isinstance(fan.driver, Driver)
            assert isinstance(fan.fanId, int)
            assert isinstance(fan.getSpeed(), int)
            assert (not fan.getSpeed() < 0) or (not fan.getSpeed() > 100)
            fan.setSpeed(100)
            assert isinstance(fan.getDirection(), str)

if __name__ == '__main__':
   unittest.main()
