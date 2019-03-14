from ..core.driver import KernelDriver
from ..core.types import PciAddr, SysfsPath

class PciKernelDriver(KernelDriver, SysfsPath):
   def __init__(self, addr, name, args=None):
      assert isinstance(addr, PciAddr)
      super(PciKernelDriver, self).__init__(name, args=args)
      self.addr = addr

   def getSysfsPath(self):
      return self.addr.getSysfsPath()
