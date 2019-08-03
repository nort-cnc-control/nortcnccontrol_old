from . import action

from common import event

class TableCoordinates(action.MCUAction):

    def __init__(self, coordinates, *args, **kwargs):
        action.MCUAction.__init__(self, *args, **kwargs)
        self.caching = False
        self.coordinates = coordinates

    def command(self):
        return "M114"

    def on_completed(self, response):
        x = response["X"]
        y = response["Y"]
        z = response["Z"]
        position = {
            "x" : x,
            "y" : y,
            "z" : z,
        }
        self.coordinates(position)

class TableEndstops(action.MCUAction):

    def __init__(self, coordinates, *args, **kwargs):
        action.MCUAction.__init__(self, *args, **kwargs)
        self.caching = False
        self.coordinates = coordinates

    def command(self):
        return "M114"

    def on_completed(self, response):
        x = response["X"]
        y = response["Y"]
        z = response["Z"]
        p = response["P"]
        position = {
            "x" : x != 0,
            "y" : y != 0,
            "z" : z != 0,
            "probe" : p != 0,
        }
        self.coordinates(position)
