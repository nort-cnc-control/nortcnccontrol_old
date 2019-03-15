class Positioning(object):

    is_moving = False
    X = None
    Y = None
    Z = None
    R = None
    I = None
    J = None
    K = None

    def __init__(self, frame):
        for cmd in frame.commands:
            if cmd.type == "X":
                if self.X != None:
                    raise Exception("X meets 2 times")
                self.X = cmd.value
                self.is_moving = True
            elif cmd.type == "Y":
                if self.Y != None:
                    raise Exception("Y meets 2 times")
                self.Y = cmd.value
                self.is_moving = True
            elif cmd.type == "Z":
                if self.Z != None:
                    raise Exception("Z meets 2 times")
                self.Z = cmd.value
                self.is_moving = True
            elif cmd.type == "R":
                if self.R != None:
                    raise Exception("R meets 2 times")
                self.R = cmd.value
            elif cmd.type == "I":
                if self.I != None:
                    raise Exception("I meets 2 times")
                self.I = cmd.value
            elif cmd.type == "J":
                if self.J != None:
                    raise Exception("J meets 2 times")
                self.J = cmd.value
            elif cmd.type == "K":
                if self.K != None:
                    raise Exception("K meets 2 times")
                self.K = cmd.value


class Feed(object):

    feed = None
        
    def __init__(self, frame):
        for cmd in frame.commands:
            if cmd.type == "F":
                if self.feed != None:
                    raise Exception("F meets 2 times")
                self.feed = cmd.value

class SpindleSpeed(object):
        
    speed = None
        
    def __init__(self, frame):
        for cmd in frame.commands:
            if cmd.type == "S":
                if self.speed != None:
                    raise Exception("S meets 2 times")
                self.speed = cmd.value

class Tool(object):

    tool = None
        
    def __init__(self, frame):
        for cmd in frame.commands:
            if cmd.type == "T":
                if self.tool != None:
                    raise Exception("T meets 2 times")
                self.tool = cmd.value

class ProgramId(object):
        
    program = None
    num = None
 
    def __init__(self, frame):
        for cmd in frame.commands:
            if cmd.type == "P":
                if self.program != None:
                    raise Exception("P meets 2 times")
                self.program = cmd.value
            if cmd.type == "L":
                if self.num != None:
                    raise Exception("L meets 2 times")
                self.num = cmd.value
        if self.program != None and self.num is None:
            self.num = 1

class LineNumber(object):

    N = None

    def __init__(self, frame):
        if len(frame.commands) == 0:
            return
        if frame.commands[0].type != 'N':
            return
            
        rep = [cmd for cmd in frame.commands[1:] if cmd.type == "N" ]
        if len(rep) > 0:
            raise Exception("N can only be first word")
        self.N = int(frame.commands[0].value)

class ExactStop(object):

    exact_stop = False

    def __init__(self, frame):
        for cmd in frame.commands:
            if cmd.type == "G" and cmd.value == 9:
                self.exact_stop = True
                break
