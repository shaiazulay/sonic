import time

from .config import Config
from .utils import JsonStoredData

RELOAD_CAUSE_HISTORY_SIZE=128

class ReloadCauseHistoryEntry(object):
   def __init__(self, reason=None):
      self.reloadReason = reason

   def __str__(self):
      return self.reloadReason

def updateReloadCausesHistory(newCauses):
   newCauses = [ReloadCauseHistoryEntry(str(cause)) for cause in newCauses]
   rebootCauses = JsonStoredData(Config().reboot_cause_file, lifespan='persistent')
   causes = []
   if rebootCauses.exist():
      causes = rebootCauses.readList(ReloadCauseHistoryEntry)
      causes.extend(newCauses)
      rebootCauses.clear()
   else:
      causes = newCauses

   if len(causes) > RELOAD_CAUSE_HISTORY_SIZE:
      causes = causes[len(causes) - RELOAD_CAUSE_HISTORY_SIZE:]

   rebootCauses.writeList(causes)

def getReloadCauseHistory():
   rebootCauses = JsonStoredData(Config().reboot_cause_file, lifespan='persistent')
   if rebootCauses.exist():
      return rebootCauses.readList(ReloadCauseHistoryEntry)
   return None

def datetimeToStr(datetime):
   return time.strftime("%Y-%m-%d %H:%M:%S",
                        time.gmtime(time.mktime(datetime.timetuple())))  + " UTC"