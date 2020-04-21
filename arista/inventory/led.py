
class Led(object):
   def getColor(self):
      raise NotImplementedError()

   def setColor(self, color):
      raise NotImplementedError()

   def getName(self):
      raise NotImplementedError()

   def isStatusLed(self):
      raise NotImplementedError()
