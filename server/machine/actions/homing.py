from . import action

class ToBeginMovement(action.MCUAction):

    def command(self):
        return "G28"
