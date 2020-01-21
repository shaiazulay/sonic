
from __future__ import absolute_import, division, print_function

from . import registerAction

@registerAction('reboot')
def doReboot(args, platform):
   import arista.utils.sonic_reboot
   arista.utils.sonic_reboot.reboot(platform.getInventory())
