import action

class WaitTool(action.Action):

    def __init__(self, tool):
        self.tool = tool

    def act(self):
        print("insert tool %i" % self.tool)

class SetSpeed(action.Action):
    def __init__(self, speed):
        self.speed = speed

    def act(self):
        print("set spindle speed %i" % self.speed)
