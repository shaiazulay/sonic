
class Watchdog(object):
   def arm(self, timeout):
      raise NotImplementedError()

   def stop(self):
      raise NotImplementedError()

   def status(self):
      raise NotImplementedError()

   def __diag__(self, ctx):
      return {
         "status": self.status() if ctx.performIo else None,
      }
