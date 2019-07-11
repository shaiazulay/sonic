from .led import LedImpl

class RookLedImpl(LedImpl):
   def __init__(self, baseName="rook_leds", colors=None, name=None, driver=None,
                **kwargs):
      self.baseName = baseName
      self.colors = colors or []
      super(RookLedImpl, self).__init__(name=name, driver=driver, **kwargs)
