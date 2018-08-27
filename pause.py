import action

class WaitResume(action.Action):

    def act(self):
        print("pause")
        return False
