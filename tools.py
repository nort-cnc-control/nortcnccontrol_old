import action

class WaitTool(action.Action):

    def __init__(self, tool):
        self.tool = tool

    def act(self):
        print("insert tool %i" % self.tool)
