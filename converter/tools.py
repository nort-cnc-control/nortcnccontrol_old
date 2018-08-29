import event

from . import action

class WaitTool(action.Action):

    def __init__(self, tool):
        action.Action.__init__(self)
        self.tool_changed = event.EventEmitter()
        self.tool = tool

    def act(self):
        self.tool_changed(self.tool)
        return False

class SetSpeed(action.Action):

    def __init__(self, speed):
        action.Action.__init__(self)
        self.speed = speed

    def act(self):
        #print("set spindle speed %i" % self.speed)
        return True
