
from ..core.log import getLogger

logging = getLogger(__name__)

def pciRescan():
   logging.info('triggering kernel pci rescan')
   with open('/sys/bus/pci/rescan', 'w') as f:
      f.write('1')

