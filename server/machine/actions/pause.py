from common import event

from . import action

class WaitResume(action.InstantAction):

    def __init__(self, **kwargs):
        action.InstantAction.__init__(self, **kwargs)
        self.paused = event.EventEmitter()
        self.is_pause = True

    def perform(self):
        self.paused()
        return False
