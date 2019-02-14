from . import action

class SpindleOff(action.ToolAction):

    def __init__(self, **kwargs):
        action.ToolAction.__init__(self, **kwargs)

    def perform(self):
        print("Spindle off")
        return True

class SpindleOn(action.ToolAction):

    def __init__(self, speed, cw, **kwargs):
        action.ToolAction.__init__(self, **kwargs)
        self.speed = speed
        self.cw = cw

    def perform(self):
        print("Spindle on, speed = %lf" % self.speed)
        return True

class SpindleSetSpeed(action.ToolAction):
    def __init__(self, speed, **kwargs):
        action.ToolAction.__init__(self, **kwargs)
        self.speed = speed

    def perform(self):
        print("Spindle speed = %lf" % self.speed)
        return True
