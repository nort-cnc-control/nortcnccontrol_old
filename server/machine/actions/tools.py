from common import event

from . import action

class WaitTool(action.InstantAction):

    def __init__(self, tool, **kwargs):
        action.InstantAction.__init__(self, **kwargs)
        self.tool_changed = event.EventEmitter()
        self.tool = tool
        self.is_pause = True

    def perform(self):
        self.tool_changed(self.tool)
        return False
