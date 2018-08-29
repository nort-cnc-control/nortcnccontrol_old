from . import action

class ToBeginMovement(action.Action):

    def make_code(self):
        res = "G28"
        print(res)
        return True
