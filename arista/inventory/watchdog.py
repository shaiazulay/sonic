
class Watchdog(object):
   def arm(self, timeout):
      raise NotImplementedError()

   def stop(self):
      raise NotImplementedError()

   def status(self):
      raise NotImplementedError()
