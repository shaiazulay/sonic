
from __future__ import absolute_import, division, print_function

import datetime

from ...tests.testing import unittest

from .. import inventory
from ..inventory import Inventory
from ..metainventory import MetaInventory, LazyInventory

class TestFan(inventory.Fan):
   def __init__(self, fanId=1, name="fan1", speed=12345, direction='forward'):
      self.fanId = fanId
      self.name = name
      self.speed = speed
      self.direction = direction

   def getName(self):
      return self.name

   def getSpeed(self):
      return self.speed

   def setSpeed(self, speed):
      self.speed = speed

   def getDirection(self):
      return self.direction

   def __eq__(self, value):
      return isinstance(value, TestFan) and self.fanId == value.fanId

class TestPsu(inventory.Psu):
   def __init__(self, psuId=1, name="psu1", presence=True, status=True):
      self.psuId = psuId
      self.name = name
      self.presence = presence
      self.status = status

   def getName(self):
      return self.name

   def getPresence(self):
      return self.presence

   def getStatus(self):
      return self.status

   def __eq__(self, value):
      return isinstance(value, TestPsu) and self.psuId == value.psuId

class TestWatchdog(inventory.Watchdog):
   def __init__(self, started=True, remaining=100, timeout=300):
      self.started = started
      self.remaining = remaining
      self.timeout = timeout

   def arm(self, timeout):
      self.timeout = timeout

   def stop(self):
      self.started = False
      self.remaining = 0

   def status(self):
      return self.started

class TestPowerCycle(inventory.PowerCycle):
   def __init__(self, powered=True):
      self.powered = powered

   def powerCycle(self):
      self.powered = not self.powered

   def __eq__(self, value):
      return isinstance(value, TestPowerCycle) and self.powered == value.powered

class TestReloadCause(inventory.ReloadCause):
   def __init__(self, name='unknown', time=datetime.datetime.now()):
      self.name = name
      self.time = time

   def getTime(self):
      return self.time

   def getCause(self):
      return self.name

class TestInterrupt(inventory.Interrupt):
   def __init__(self, name='unknown', status=False):
      self.name = name
      self.status = status
      self.path = '/test/path'

   def set(self):
      self.status = True

   def clear(self):
      self.status = False

   def getFile(self):
      return self.path

class TestReset(inventory.Reset):
   def __init__(self, name='unknown', reset=False):
      self.name = name
      self.reset = reset

   def read(self):
      return self.reset

   def resetIn(self):
      self.reset = True

   def resetOut(self):
      self.reset = False

   def getName(self):
      return self.name

class TestPhy(inventory.Phy):
   def __init__(self, phyId=1, reset=False):
      self.phyId = phyId
      self.reset = reset

   def getReset(self):
      return self.reset

   def __eq__(self, value):
      return isinstance(value, TestPhy) and self.phyId == value.phyId

class TestLed(inventory.Led):
   def __init__(self, name='unknown', color='green', status=True):
      self.name = name
      self.color = color
      self.status = status

   def getColor(self):
      return self.color

   def setColor(self, color):
      self.color = color

   def getName(self):
      return self.name

   def isStatusLed(self):
      return self.status

   def __eq__(self, value):
      return isinstance(value, TestLed) and self.name == value.name

class TestSlot(inventory.Slot):
   def __init__(self, name='unknown', present=True):
      self.name = name
      self.present = present

   def getPresence(self):
      return self.present

   def __eq__(self, value):
      return isinstance(value, TestSlot) and self.name == value.name

class TestXcvr(inventory.Xcvr):
   def __init__(self, portId=0, xcvrType=inventory.Xcvr.QSFP, name="unknown",
                presence=True, lpMode=False, intr=None, reset=None):
      self.portId = portId
      self.xcvrId = portId
      self.xcvrType = xcvrType
      self.name = name
      self.presence = presence
      self.lpMode = lpMode
      self.intr = intr
      self.reset = reset or TestReset('xcvr%d' % portId)

   def getName(self):
      return self.name

   def getPresence(self):
      return self.presence

   def getLowPowerMode(self):
      return self.lpMode

   def setLowPowerMode(self, value):
      self.lpMode = value

   def getInterruptLine(self):
      return self.intr

   def getReset(self):
      # TODO: introduce unsupported feature exceptions for inventory
      # if self.xcvrType == inventory.Xcvr.QSFP:
      #    raise FeatureNotSupported()
      return self.reset

class TestTemp(inventory.Temp):
   def __init__(self, diode=1, temperature=30, lowThreshold=10, highThreshold=50):
      self.diode = diode
      self.temperature = temperature
      self.lowThreshold = lowThreshold
      self.highThreshold = highThreshold

   def getTemperature(self):
      return self.temperature

   def getLowThreshold(self):
      return self.lowThreshold

   def setLowThreshold(self, value):
      self.lowThreshold = value * 1000

   def getHighThreshold(self):
      return self.highThreshold

   def setHighThreshold(self, value):
      self.highThreshold = value * 1000

   def __eq__(self, value):
      return isinstance(value, TestTemp) and self.diode == value.diode

class InventoryTest(unittest.TestCase):
   def _populateTestInventory(self, inv):
      inv.addPorts(
         sfps=list(range(0, 2)),
         qsfps=list(range(2, 4)),
         osfps=list(range(4, 6)),
      )
      xcvrs = [
         TestXcvr(0, TestXcvr.SFP, "SFP-1G-SX"),
         TestXcvr(1, TestXcvr.SFP, "CAB-SFP-SFP-1M"),
         TestXcvr(2, TestXcvr.QSFP, "CAB-Q-Q-100G-1M"),
         TestXcvr(3, TestXcvr.QSFP, "QSFP-100G-CWDM4"),
         TestXcvr(4, TestXcvr.OSFP, "AB-O-O-400G-1M"),
         TestXcvr(5, TestXcvr.OSFP, "AOC-O-O-400G-3M"),
      ]
      for xcvr in xcvrs:
         led = TestLed('%s%d' % (xcvr.typeStr(xcvr.xcvrType), xcvr.portId))
         inv.addLed(led)
         inv.addXcvr(xcvr)

      inv.addStatusLeds([
         TestLed('status'),
         TestLed('fans'),
         TestLed('psu1'),
      ])
      inv.addResets({
         'internet': TestReset('internet'),
         'humanity': TestReset('humanity'),
      })
      inv.addPsus([
         TestPsu(1, 'psu1'),
         TestPsu(2, 'psu2'),
      ])
      inv.addFans([
         TestFan(1, 'fan1'),
         TestFan(2, 'fan2'),
         TestFan(3, 'fan3'),
         TestFan(4, 'fan4'),
      ])
      inv.addPowerCycle(TestPowerCycle())
      inv.addWatchdog(TestWatchdog())
      inv.addInterrupt('intr', TestInterrupt())
      inv.addPhy(TestPhy())
      inv.addSlot(TestSlot())
      inv.addTemp(TestTemp(diode=1))
      inv.addTemp(TestTemp(diode=2))

   def _populateSmallTestInventory(self, inv):
      inv.addPsus([
         TestPsu(3, 'psu3'),
         TestPsu(4, 'psu4'),
      ])

   def _getTestInventory(self, populate=True):
      inv = Inventory()
      if populate:
         self._populateTestInventory(inv)
      return inv

   def _getSmallInventory(self):
      inv = self._getTestInventory(populate=False)
      self._populateSmallTestInventory(inv)
      return inv

   def _getFullInventory(self):
      inv = self._getTestInventory()
      self._populateSmallTestInventory(inv)
      return inv

   def _getTestMetaInventory(self, ):
      inv = self._getTestInventory()
      meta = MetaInventory(invs=[inv])
      return meta

   def _iterInventoryGetters(self):
      for attr in dir(Inventory):
         if attr.startswith('get') and attr.endswith( 's' ):
            yield attr

   def assertInventoryEqual(self, inv1, inv2):
      for attr in self._iterInventoryGetters():
         v1 = getattr(inv1, attr)()
         v2 = getattr(inv2, attr)()
         self.assertEqual(type(v1), type(v2))
         if isinstance(v1, (list, dict, set)):
            for item in v1:
               self.assertIn(item, v2)
         else:
            self.assertEqual(v1, v2)

   def testInventory(self):
      inv = self._getTestInventory()
      inv.getXcvrs()

   def testSimpleMetaInventory(self):
      meta = self._getTestMetaInventory()
      with self.assertRaises(AttributeError):
         meta.nonExistant()
      self.assertDictEqual(meta.getXcvrs(), meta.invs[0].getXcvrs())

   def testGeneratorMetaInventory(self):
      inv1 = self._getTestInventory()
      inv2 = self._getSmallInventory()
      invs = self._getFullInventory()

      def generator():
         for inv in [ inv1, inv2 ]:
            yield inv

      meta = MetaInventory(invs=iter(generator()))
      self.assertListEqual(meta.getPsus(), invs.getPsus())

   def testLazyInventory(self):
      lazy = LazyInventory()
      self.assertEqual(len(lazy.__dict__), 0)
      self._populateTestInventory(lazy)
      self.assertNotEqual(len(lazy.__dict__), 0)

      inv = self._getTestInventory()
      self.assertGreaterEqual(len(inv.__dict__), len(lazy.__dict__))

   def testLazyMetaInventory(self):
      lazy1 = LazyInventory()
      self._populateTestInventory(lazy1)
      # lazyLen1 = len(lazy1.__dict__)
      lazy2 = LazyInventory()
      self._populateSmallTestInventory(lazy2)
      # lazyLen2 = len(lazy2.__dict__)
      meta = MetaInventory(invs=[lazy1, lazy2])

      inv = self._getFullInventory()
      self.assertInventoryEqual(inv, meta)

      # self.assertEqual(lazyLen1, len(lazy1.__dict__))
      # self.assertEqual(lazyLen2, len(lazy2.__dict__))

   def testLegacyLazyMetaInventory(self):
      inv = self._getTestInventory()
      lazy = LazyInventory()
      self._populateSmallTestInventory(lazy)
      meta = MetaInventory(invs=[inv, lazy])

      inv = self._getFullInventory()
      self.assertInventoryEqual(inv, meta)

   def testEmptyMetaInventory(self):
      meta = MetaInventory()
      inv = Inventory()
      for attr in self._iterInventoryGetters():
         metaval = getattr(meta, attr)()
         invval = getattr(inv, attr)()
         self.assertEquals(metaval, invval)

if __name__ == '__main__':
   unittest.main()
