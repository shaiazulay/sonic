#!/usr/bin/env python
from __future__ import absolute_import

try:
   from mock import patch
except ImportError:
   from unittest.mock import patch
import unittest

from arista.accessors.fan import FanImpl
from arista.accessors.led import LedImpl
from arista.accessors.xcvr import XcvrImpl

from arista.components.scd import ScdInterruptRegister

from arista.core import utils
from arista.core.driver import Driver
from arista.core.inventory import Psu, Xcvr
from arista.core.platform import getPlatforms
from arista.core.types import I2cAddr

from arista.drivers.i2c import I2cKernelDriver
from arista.drivers.psu import UpperlakePsuDriver
from arista.drivers.scd import ScdKernelDriver
from arista.drivers.sysfs import SysfsDriver

import arista.platforms

from tests.common import getLogger

def mock_i2cBusFromName(name, idx=0, force=False):
   assert isinstance(name, str)
   return 0

# TODO: remove this type of simulation testing
def mock_inSimulation():
   return False

def mock_locateHwmonPath(searchPath, prefix):
   assert isinstance(searchPath, str)
   assert isinstance(prefix, str)
   return 'mock path'

def mock_writeConfig(path, data):
   assert isinstance(path, str)
   assert isinstance(data, (list, dict))

def mock_writeComponents(self, components, filename):
   assert components
   assert filename

def mock_read(self, name, path=None):
   assert name
   return '1'

def mock_write(self, name, value, path=None):
   assert name
   assert value != None

def mock_getPsuStatus(self, psu):
   assert psu
   assert isinstance(psu.psuId, int)
   return True

def mock_readReg(self, reg):
   assert reg
   return None

def mock_getStatus(self):
   return True

def mock_waitReady(self):
   return True

def mock_return(self):
   return

@patch('arista.drivers.scd.i2cBusFromName', mock_i2cBusFromName)
@patch('arista.core.utils.inSimulation', mock_inSimulation)
@patch('arista.core.utils.locateHwmonPath', mock_locateHwmonPath)
@patch('arista.core.utils.writeConfig', mock_writeConfig)
@patch.object(I2cKernelDriver, 'setup', mock_return)
@patch.object(ScdInterruptRegister, 'readReg', mock_readReg)
@patch.object(ScdInterruptRegister, 'setup', mock_return)
@patch.object(ScdKernelDriver, 'finish', mock_return)
@patch.object(ScdKernelDriver, 'waitReady', mock_waitReady)
@patch.object(ScdKernelDriver, 'writeComponents', mock_writeComponents)
@patch.object(SysfsDriver, 'read', mock_read)
@patch.object(SysfsDriver, 'write', mock_write)
@patch.object(UpperlakePsuDriver, 'getPsuStatus', mock_getPsuStatus)
@patch.object(utils.FileWaiter, 'waitFileReady', mock_return)
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
      cls.ledColors = ['off', 'green', 'red', 'yellow']

   def _testLed(self, led):
      assert isinstance(led, LedImpl)
      assert isinstance(led.name, str)
      name = led.getName()
      assert name == led.name
      assert isinstance(led.driver, Driver)
      color = led.getColor()
      assert color in self.ledColors
      for color in self.ledColors:
         led.setColor(color)

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
            leds = xcvr.getLeds()
            for led in leds:
               self._testLed(led)

   def testPsus(self):
      for name, inventory in self.inventories.items():
         self.logger.info('Testing PSUs for platform %s', name)
         for psu in inventory.getPsus():
            assert isinstance(psu, Psu)
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
            assert isinstance(fan.led, LedImpl)
            assert isinstance(fan.getSpeed(), int)
            assert (not fan.getSpeed() < 0) or (not fan.getSpeed() > 100)
            fan.setSpeed(100)
            assert isinstance(fan.getDirection(), str)
            led = fan.getLed()
            assert led == fan.led
            self._testLed(led)

if __name__ == '__main__':
   unittest.main()
