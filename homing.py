import action

class ToBeginMovement(action.Action):

    def make_code(self):
        res = "G28"
        if self.x:
            res += " X0"
        if self.y:
            res += " Y0"
        if self.z:
            res += " Z0"
        print(res)
        
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z
