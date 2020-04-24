
from .tmp468 import Tmp468

class Tmp464(Tmp468):
   def __init__(self, *args, **kwargs):
      kwargs['kname'] = 'tmp464'
      kwargs['remoteCount' ] = 4
      super(Tmp464, self).__init__(*args, **kwargs)
