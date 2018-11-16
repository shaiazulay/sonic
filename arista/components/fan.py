import os
import logging

from ..core.inventory import Fan

class SysfsFan(Fan):
   def __init__(self, hwmonPath, index):
      self.hwmonPath = hwmonPath
      self.index = index
      self.pwmPath = os.path.join(hwmonPath, "pwm%d" % index)

   def getSpeed(self):
      with open(self.pwmPath, "r") as pwm:
         return int(pwm.read())

   def setSpeed(self, speed):
      logging.info("Setting fan %d to speed %d", self.index, speed)
      with open(self.pwmPath, "w") as pwm:
         pwm.write(speed)
