from . import action

from common import event

class Finish(action.InstantAction):

    def __init__(self, **kwargs):
        action.InstantAction.__init__(self, **kwargs)
        self.finished = event.EventEmitter()

    def perform(self):
        self.finished(self)
        return False

