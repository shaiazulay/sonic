import os

from .sysfs import LedSysfsDriver

class RookLedSysfsDriver(LedSysfsDriver):
   def getLedColor(self, led):
      onColors = []
      for color in led.colors:
         ledName = "%s:%s:%s" % (led.baseName, color, led.name)
         path = os.path.join(self.sysfsPath, ledName, 'brightness')
         if self.read(ledName, path=path) == '1':
            onColors.append(color)
      return ', '.join(onColors) or 'off'

   def setLedColor(self, led, value):
      if value not in led.colors:
         return
      for color in led.colors:
         ledName = "%s:%s:%s" % (led.baseName, color, led.name)
         path = os.path.join(self.sysfsPath, ledName, 'brightness')
         self.write(ledName, '0', path=path)
      ledName = "%s:%s:%s" % (led.baseName, value, led.name)
      path = os.path.join(self.sysfsPath, ledName, 'brightness')
      self.write(ledName, '1', path=path)
