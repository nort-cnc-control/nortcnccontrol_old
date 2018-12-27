from . import action

class ToBeginMovement(action.MCUAction):

    def command(self):
        return "G28"

class ProbeMovement(action.MCUAction):
    
    def command(self):
        return "G30"
