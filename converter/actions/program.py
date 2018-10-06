import event
from . import action

class Finish(action.InstantAction):

    def __init__(self, **kwargs):
        action.InstantAction.__init__(self, **kwargs)
        self.finished = event.EventEmitter()

    def perform(self):
        self.finished(self)
        return False

    def emulate(self):
        print("Finish")