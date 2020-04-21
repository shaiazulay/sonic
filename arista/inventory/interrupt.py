
class Interrupt(object):
   def set(self):
      raise NotImplementedError()

   def clear(self):
      raise NotImplementedError()

   def getFile(self):
      raise NotImplementedError()
