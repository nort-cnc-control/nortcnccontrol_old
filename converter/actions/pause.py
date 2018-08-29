import event

from . import action

class WaitResume(action.Action):

    def __init__(self, **kwargs):
        action.Action.__init__(self, **kwargs)
        self.paused = event.EventEmitter()

    def act(self):
        self.paused()
        self.completed = True
        return False
