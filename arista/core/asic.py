
import os
import time

from .component import DEFAULT_WAIT_TIMEOUT, PciComponent
from .log import getLogger
from .utils import klog, inSimulation
from ..libs.pci import pciRescan

logging = getLogger(__name__)

ASIC_YIELD_TIME = os.getenv( 'ASIC_YIELD_TIME', 2 )

class SwitchChip(PciComponent):
   def __init__(self, addr, **kwargs):
      super(SwitchChip, self).__init__(addr=addr, **kwargs)

   def __str__(self):
      return '%s(addr=%s)' % (self.__class__.__name__, self.addr)

   def pciRescan(self):
      pciRescan()

   def isInReset(self):
      return self.resetGpio()

   def waitForIt(self, timeout=DEFAULT_WAIT_TIMEOUT):
      begin = time.time()
      end = begin + timeout
      rescanTime = begin + (timeout / 2)
      devPath = self.addr.getSysfsPath()

      logging.debug('waiting for switch chip %s', devPath)
      if inSimulation():
         return True

      klog('waiting for switch chip')
      while True:
         now = time.time()
         if now > end:
            break
         if os.path.exists(devPath):
            logging.debug('switch chip is ready')
            klog('switch chip is ready')
            time.sleep(ASIC_YIELD_TIME)
            klog('yielding...')
            return True
         if now > rescanTime:
            self.pciRescan()
            rescanTime = end
         time.sleep(0.1)

      logging.error('timed out waiting for the switch chip %s', devPath)
      return False
