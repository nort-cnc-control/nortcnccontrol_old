from . import action

class TableReset(action.Action):
    def __init__(self, sender):
        self.sender = sender
        self.is_pause = True
    
    def act(self):
        self.sender.send_command("M999", wait=False)
        return False

class TableUnlock(action.MCUAction):

    def __init__(self, *args, **kwargs):
        action.MCUAction.__init__(self, *args, **kwargs)
        self.caching = False

    def command(self):
        return "M800"
