import time

class TimeoutError(Exception):
   def __init__(self, msg, code=1):
      self.msg = msg
      self.code = code

   def __str__(self):
      return 'TimeoutError: %s (code %d)' % (self.msg, self.code)

def waitFor(func, description=None, timeout=60, sleep=False,
            args=None, kwargs=None):
   '''Run func and return if it's True. Otherwise, exit after timeout seconds.
      Inputs: timeout: in second.
              description: printed out if timeout occurs.
              sleep: True if we want to avoid busy waiting.
              args and kwargs: are inputs for func.
      Outputs: the output of func if it's done, othewise False.
   '''
   if args is None:
      args = ()
   if kwargs is None:
      kwargs = {}

   def _now():
      now_in_milli_sec = int(round(time.time() * 1000))
      return now_in_milli_sec

   start = _now()
   end = start + timeout * 1000
   delay = 0.005
   maxDelay = 1
   while True:
      result = func(*args, **kwargs)
      if result:
         return result
      delay *= 2
      if delay > maxDelay:
         delay = maxDelay
      now_ = _now()
      if now_ + delay > end:
         delay = end - now_
         if delay <= 0:
            if not description:
               description = func.__name__
            raise TimeoutError("Timed out waiting for %s" % description)
      if sleep:
         time.sleep(delay)
   return False
