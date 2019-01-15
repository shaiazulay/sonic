import select
import time

from ..core import platform as core_platform
from .. import platforms

try:
    from sonic_sfp.sfputilbase import SfpUtilBase
except ImportError as e:
    raise ImportError("%s - required module not found" % str(e))


def getSfpUtil():
    platform = core_platform.getPlatform()
    inventory = platform.getInventory()

    class SfpUtil(SfpUtilBase):
        """Platform-specific SfpUtil class"""

        @property
        def port_start(self):
            return inventory.portStart

        @property
        def port_end(self):
            return inventory.portEnd

        @property
        def osfp_ports(self):
            return inventory.osfpRange

        @property
        def qsfp_ports(self):
            return inventory.qsfpRange

        # XXX: defining the sfp_ports property currently can't be done as
        #      it affect the code logic of the sfputil tool by preventing
        #      the qsfp ports from being detected
        #@property
        #def sfp_ports(self):
        #    return inventory.sfpRange

        @property
        def port_to_eeprom_mapping(self):
            return inventory.getPortToEepromMapping()

        @property
        def port_to_i2cbus_mapping(self):
            return inventory.getPortToI2cAdapterMapping()

        def __init__(self):
            SfpUtilBase.__init__(self)

        def get_presence(self, port_num):
            if not self._is_valid_port(port_num):
                return False

            return inventory.getXcvr(port_num).getPresence()

        def get_low_power_mode(self, port_num):
            if not self._is_valid_port(port_num):
                return False

            return inventory.getXcvr(port_num).getLowPowerMode()

        def set_low_power_mode(self, port_num, lpmode):
            if not self._is_valid_port(port_num):
                return False

            try:
               return inventory.getXcvr(port_num).setLowPowerMode(lpmode)
            except:
               #print('failed to set low power mode for xcvr %d' % port_num)
               return False

        def reset(self, port_num):
            if not self._is_valid_port(port_num):
                return False

            xcvr = inventory.getXcvr(port_num).getReset()
            if xcvr is None:
               return False

            try:
               xcvr.resetIn()
            except:
               #print('failed to put xcvr %d in reset' % port_num)
               return False

            # Sleep 1 second to allow it to settle
            time.sleep(1)

            try:
               xcvr.resetOut()
            except:
               #print('failed to take xcvr %d out of reset' % port_num)
               return False

            return True

        def get_transceiver_change_event(self, timeout=0):
            xcvrs = inventory.getXcvrs()
            epoll = select.epoll()
            openFiles = []
            ret = {}
            try:
               # Clear the interrupt masks
               for xcvr in xcvrs.values():
                  intr = xcvr.getInterruptLine()
                  if not intr:
                     continue
                  xcvr.getPresence()
                  intr.clear()
                  openFile = open(intr.getFile())
                  openFiles.append((xcvr, openFile))
                  epoll.register(openFile.fileno(), select.EPOLLIN)
               pollRet = epoll.poll(timeout=timeout if timeout != 0 else -1)
               if pollRet:
                  pollRet = dict(pollRet)
                  for xcvr, openFile in openFiles:
                     if openFile.fileno() in pollRet:
                        ret[str(xcvr.portNum)] = '1' if xcvr.getPresence() else '0'
                  return True, ret
            finally:
               for _, openFile in openFiles:
                  openFile.close()
               epoll.close()

            return False, {}

    return SfpUtil
