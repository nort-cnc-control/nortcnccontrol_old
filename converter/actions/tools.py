import event

from . import action

class WaitTool(action.InstantAction):

    def __init__(self, tool, **kwargs):
        action.InstantAction.__init__(self, **kwargs)
        self.tool_changed = event.EventEmitter()
        self.tool = tool

    def perform(self):
        self.tool_changed(self.tool)
        return False

    def emulate(self):
        print("Waiting tool %i" % self.tool)

class SetSpeed(action.MCUAction):

    def __init__(self, speed, **kwargs):
        action.MCUAction.__init__(self, **kwargs)
        self.speed = speed

    def emit_command(self):
        return "S%i" % self.speed
