
import logging
import os
import time

from ..core.component import Component, DEFAULT_WAIT_TIMEOUT, ASIC_YIELD_TIME
from ..core.driver import KernelDriver
from ..core.utils import klog, inSimulation
from ..core.types import PciAddr, SysfsPath

from ..drivers.i2c import I2cKernelDriver

class PciComponent(Component):
   def __init__(self, **kwargs):
      super(PciComponent, self).__init__(**kwargs)

class I2cComponent(Component):
   def __init__(self, driver=I2cKernelDriver, **kwargs):
      super(I2cComponent, self).__init__(driver=driver, **kwargs)

# Do not use this class as it is being depreciated
class I2cKernelComponent(I2cComponent):
   def __init__(self, addr, name, waitFile=None, waitTimeout=None, **kwargs):
      super(I2cKernelComponent, self).__init__(addr=addr, name=name,
                                               waitFile=waitFile,
                                               waitTimeout=waitTimeout, **kwargs)

class SwitchChip(PciComponent):
   def __init__(self, addr, **kwargs):
      super(SwitchChip, self).__init__(addr=addr, **kwargs)
      
   def pciRescan(self):
      logging.info('triggering kernel pci rescan')
      with open('/sys/bus/pci/rescan', 'w') as f:
         f.write('1\n')

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
