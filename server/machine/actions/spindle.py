from . import action

class SpindleOff(action.ToolAction):

    def __init__(self, sender, **kwargs):
        action.ToolAction.__init__(self, **kwargs)
        self.sender = sender

    def perform(self):
        print("Spindle off")
        self.sender.stop()
        return True

class SpindleOn(action.ToolAction):

    def __init__(self, sender, speed, cw, **kwargs):
        action.ToolAction.__init__(self, **kwargs)
        self.sender = sender
        self.speed = speed
        self.cw = cw

    def perform(self):
        print("Spindle on, speed = %lf" % self.speed)
        self.sender.set_speed(self.speed)
        if self.cw:
            self.sender.start_forward()
        else:
            self.sender.start_reverse()
        return True

class SpindleSetSpeed(action.ToolAction):

    def __init__(self, sender, speed, **kwargs):
        action.ToolAction.__init__(self, **kwargs)
        self.sender = sender
        self.speed = speed

    def perform(self):
        print("Spindle speed = %lf" % self.speed)
        self.sender.set_speed(self.speed)
        return True

