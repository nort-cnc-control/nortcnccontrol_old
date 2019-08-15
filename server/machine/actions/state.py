import euclid3

from . import action

from common import event

class TableCoordinates(action.MCUAction):

    def __init__(self, sender, coordinates_cb, *args, **kwargs):
        action.MCUAction.__init__(self, sender, *args, **kwargs)
        self.caching = False
        self.coordinates = coordinates_cb

    def command(self):
        return "M114"

    def on_completed(self, response):
        try:
            x = response["X"]
            y = response["Y"]
            z = response["Z"]
        except:
            return
        position = {
            "x" : x,
            "y" : y,
            "z" : z,
        }
        self.coordinates(position)

class TableEndstops(action.MCUAction):

    def __init__(self, sender, endstops, *args, **kwargs):
        action.MCUAction.__init__(self, sender, *args, **kwargs)
        self.caching = False
        self.endstops = endstops

    def command(self):
        return "M114"

    def on_completed(self, response):
        try:
            x = response["X"]
            y = response["Y"]
            z = response["Z"]
            p = response["P"]
        except:
            return
        endstops = {
            "x" : x != 0,
            "y" : y != 0,
            "z" : z != 0,
            "probe" : p != 0,
        }
        self.endstops(endstops)

class CurrentCoordinateSystem(action.Action):
    def __init__(self, csupdate_cb, cs, offset, *args, **kwargs):
        action.Action.__init__(self, *args, **kwargs)
        self.offset = offset
        self.cs = cs
        self.csupdate_cb = csupdate_cb

    def act(self):
        print("SET CS = ", self.cs, self.offset)
        self.csupdate_cb(self.cs, self.offset)
        self.completed.set()
        self.finished.set()
        self.action_completed(self)
            