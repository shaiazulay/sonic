
from __future__ import print_function

class Renderer(object):
   def __init__(self, name):
      self.name = name

   def renderText(self, show):
      raise NotImplementedError

   def data(self, show):
      '''Output for JSON, recommended to use for text as well'''
      raise NotImplementedError

class Show(object):

   TXT = 'text'
   JSON = 'json'

   def __init__(self, outputFormat=None):
      self.outputFormat = outputFormat
      self.inventories = []

   def addInventory(self, inventory, **metadata):
      self.inventories.append((inventory, metadata))

   def renderText(self, *renderers):
      for r in renderers:
         r.renderText(self)

   def renderJson(self, *renderers):
      data = {
         "version": 1,
         "renderers": {
            r.name : r.data(self) for r in renderers
         },
      }

      import json
      print(json.dumps(data))

   def render(self, *renderers):
      if self.outputFormat == self.TXT:
         self.renderText(*renderers)
      elif self.outputFormat == self.JSON:
         self.renderJson(*renderers)
