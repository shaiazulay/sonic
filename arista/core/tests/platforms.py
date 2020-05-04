from __future__ import absolute_import

from ...tests.testing import unittest, patch
from ...tests.logging import getLogger

from ...accessors.fan import FanImpl
from ...accessors.led import LedImpl
from ...accessors.temp import TempImpl
from ...accessors.xcvr import XcvrImpl

from ...components.scd import ScdInterruptRegister

from ...descs.sensor import SensorDesc

from ...drivers.i2c import I2cKernelDriver
from ...drivers.psu import UpperlakePsuDriver
from ...drivers.scd import ScdKernelDriver
from ...drivers.sysfs import SysfsDriver

from ...inventory.psu import Psu
from ...inventory.xcvr import Xcvr

from .. import utils
from ..driver import Driver
from ..fixed import FixedSystem
from ..platform import getPlatformSkus
from ..types import I2cAddr

from ... import platforms as _

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

def mock_iterAll(self):
   return []

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
      for name, platform in getPlatformSkus().items():
         if not issubclass(platform, FixedSystem):
            continue
         self.logger.info('Testing setup for platform %s', name)
         assert platform
         platform = platform()
         platform.setup()
         assert platform
         self.logger.info('Setting inventory for platform %s', name)
         inventory = platform.getInventory()
         assert inventory

   def testXcvrs(self):
      for name, platform in getPlatformSkus().items():
         if not issubclass(platform, FixedSystem):
            continue
         inventory = platform().getInventory()
         self.logger.info('Testing transceivers for platform %s', name)
         for index, xcvr in inventory.getXcvrs().items():
            self.logger.debug('Testing xcvr index %s', index)
            assert isinstance(xcvr, XcvrImpl)
            assert isinstance(xcvr.name, str)
            assert isinstance(xcvr.driver, Driver)
            assert isinstance(xcvr.addr, I2cAddr)
            assert xcvr.xcvrType in [Xcvr.SFP, Xcvr.QSFP, Xcvr.OSFP]
            assert isinstance(xcvr.xcvrId, int)
            assert isinstance(xcvr.getName(), str)
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
      for name, platform in getPlatformSkus().items():
         if not issubclass(platform, FixedSystem):
            continue
         inventory = platform().getInventory()
         self.logger.info('Testing PSUs for platform %s', name)
         for psu in inventory.getPsus():
            assert isinstance(psu, Psu)
            assert isinstance(psu.psuId, int)
            assert isinstance(psu.getName(), str)
            assert isinstance(psu.getPresence(), bool)
            assert isinstance(psu.getStatus(), bool)

   def testFans(self):
      for name, platform in getPlatformSkus().items():
         if not issubclass(platform, FixedSystem):
            continue
         inventory = platform().getInventory()
         self.logger.info('Testing fans for platform %s', name)
         for fan in inventory.getFans():
            assert isinstance(fan, FanImpl)
            assert isinstance(fan.driver, Driver)
            assert isinstance(fan.fanId, int)
            assert isinstance(fan.led, LedImpl)
            assert isinstance(fan.getPresence(), bool)
            assert isinstance(fan.getStatus(), bool)
            assert isinstance(fan.getName(), str)
            assert isinstance(fan.getSpeed(), int)
            assert (not fan.getSpeed() < 0) or (not fan.getSpeed() > 100)
            fan.setSpeed(100)
            assert isinstance(fan.getDirection(), str)
            led = fan.getLed()
            assert led == fan.led
            self._testLed(led)

   def testTemps(self):
      for name, platform in getPlatformSkus().items():
         if not issubclass(platform, FixedSystem):
            continue
         inventory = platform().getInventory()
         self.logger.info('Testing fans for platform %s', name)
         for temp in inventory.getTemps():
            assert isinstance(temp, TempImpl)
            assert isinstance(temp.driver, Driver)
            assert isinstance(temp.sensor, SensorDesc)
            assert isinstance(temp.name, str)
            assert isinstance(temp.getTemperature(), float)
            assert ((not temp.getTemperature() < 0) and
                    (not temp.getTemperature() > 200))
            assert isinstance(temp.getLowThreshold(), float)
            assert ((not temp.getLowThreshold() < 0) and
                    (not temp.getLowThreshold() > 200))
            temp.setLowThreshold(10)
            assert isinstance(temp.getHighThreshold(), float)
            assert ((not temp.getTemperature() < 0) and
                    (not temp.getTemperature() > 200))
            temp.setHighThreshold(50)

   def testComponents(self):
      def _testSubcomponentPriority(component):
         for sub in component.components:
            assert sub.priority >= component.priority
            _testSubcomponentPriority(sub)

      for name, platform in getPlatformSkus().items():
         if not issubclass(platform, FixedSystem):
            continue
         self.logger.info('Testing components priority for platform %s', name)
         for component in platform().iterComponents():
            _testSubcomponentPriority(component)

if __name__ == '__main__':
   unittest.main()
