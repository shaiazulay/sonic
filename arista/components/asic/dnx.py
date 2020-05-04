
import time

from ...core.asic import SwitchChip

DNX_CHIP_SYS_PCIE_RESET_TIME = 0.1

class DnxSwitchChip(SwitchChip):
   def resetIn(self):
      self.resetGpio(True)
      time.sleep(DNX_CHIP_SYS_PCIE_RESET_TIME)
      self.pcieResetGpio(True)

   def resetOut(self):
      self.resetGpio(False)
      time.sleep(DNX_CHIP_SYS_PCIE_RESET_TIME)
      self.pcieResetGpio(False)
