
from . import Renderer

class ShowEnvironment(Renderer):
   def __init__(self):
      super(ShowEnvironment, self).__init__('environment')

   def data(self, show):
      data = []
      for inventory, _ in show.inventories:
         prefix = '' # FIXME inventory name required
         for temp in inventory.getTemps():
            data.append({
               'name': '%s%s' % (prefix, temp.sensor.name),
               'temp': temp.getTemperature(),
               'target': temp.sensor.target,
            })
      return data

   def renderText(self, show):
      for sensor in self.data(show):
         print('%-50s %-8s %-6s' % (
            sensor['name'],
            sensor['temp'],
            sensor['target'],
         ))
