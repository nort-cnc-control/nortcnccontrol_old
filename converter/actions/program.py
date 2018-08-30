from . import action

class Finish(action.InstantAction):

    def perform(self):
        return False
