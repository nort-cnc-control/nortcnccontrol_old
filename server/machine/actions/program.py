from . import action

from common import event

class Finish(action.InstantAction):

    def __init__(self, **kwargs):
        action.InstantAction.__init__(self, **kwargs)
        self.performed = event.EventEmitter()
        self.is_pause = True

    def perform(self):
        self.performed(self)
        return False
