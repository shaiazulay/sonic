from ..core.driver import KernelDriver

class PciKernelDriver(KernelDriver):
   def __init__(self, addr=None, **kwargs):
      self.addr = addr
      super(PciKernelDriver, self).__init__(**kwargs)
