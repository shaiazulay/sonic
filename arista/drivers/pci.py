import os

from ..core.driver import KernelDriver
from ..core.utils import FileWaiter, MmapResource

class PciKernelDriver(KernelDriver):
   def __init__(self, addr=None, path=None, registerCls=None, **kwargs):
      self.addr = addr
      self.regs = registerCls(self) if registerCls is not None else None
      self.mmap_ = None
      super(PciKernelDriver, self).__init__(**kwargs)

   @property
   def mmap(self):
      if self.mmap_ is None:
         path = os.path.join(self.addr.getSysfsPath(), "resource0")
         if not FileWaiter(path, 5).waitFileReady():
            raise IOError('Mmap failed because file %s doesn\'t exist' % path)
         self.mmap_ = MmapResource(path)
         if not self.mmap_.map():
            raise IOError('Failed to mmap file %s' % path)
      return self.mmap_

   def write(self, addr, value):
      self.mmap.write32(addr, value)

   def read(self, addr):
      return self.mmap.read32(addr)
