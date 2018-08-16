#/usr/bin/env python3

import abc
import euclid3

class Action(object):
    @abc.abstractmethod
    def make_code(self):
        pass
    
    def is_moving(self):
        return False

class Movement(Action):
    def is_moving(self):
        return True

    @abc.abstractmethod
    def dir0(self):
        return None

    @abc.abstractmethod
    def dir1(self):
        return None

    def __init__(self, feed, acc):
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = acc

class LinearMovement(Movement):

    def make_code(self):
        g1 = "G01 F%i P%i L%i " % (self.feed, self.feed0, self.feed1)
        g2 = "X%.2f Y%.2f Z%.2f" % (self.delta.x, self.delta.y, self.delta.z)
        return g1 + g2

    def __init__(self, delta, feed, acc):
        Movement.__init__(self, feed=feed, acc=acc)
        self.delta = delta
        self.gcode = None
        if self.delta.magnitude() > 0:
            self.dir = self.delta / self.delta.magnitude()
        else:
            self.dir = euclid3.Vector3()
    
    def dir0(self):
        return self.dir

    def dir1(self):
        return self.dir

class SetAcceleration(Action):

    def __init__(self, acc):
        self.acc = int(acc)

    def make_code(self):
        return "M204 T%i" % self.acc

class ToBeginMovement(Action):

    def make_code(self):
        res = "G28"
        if self.x:
            res += " X0"
        if self.y:
            res += " Y0"
        if self.z:
            res += " Z0"
        return res
        
    def __init__(self, x, y, z):
        self.x = x
        self.y = y
        self.z = z

class Machine(object):
    outcode = []
    actions = []
    feed = 1
    acc = 10
    pos = euclid3.Vector3()
    relative = False

    def __init__(self):
        self.curaction = self.__none

    def __none(self, cmds):
        pass

    def __move(self, cmds):
        newpos = self.pos
        if self.relative:
            for cmd in cmds:
                if cmd.type == "X":
                    newpos = euclid3.Vector3(cmd.value + newpos.x, newpos.y, newpos.z)
                elif cmd.type == "Y":
                    newpos = euclid3.Vector3(newpos.x, cmd.value + newpos.y, newpos.z)
                elif cmd.type == "Z":
                    newpos = euclid3.Vector3(newpos.x, newpos.y, newpos.z + cmd.value)
        else:
            for cmd in cmds:
                if cmd.type == "X":
                    newpos = euclid3.Vector3(cmd.value, newpos.y, newpos.z)
                elif cmd.type == "Y":
                    newpos = euclid3.Vector3(newpos.x, cmd.value, newpos.z)
                elif cmd.type == "Z":
                    newpos = euclid3.Vector3(newpos.x, newpos.y, cmd.value)
        for cmd in cmds:
            if cmd.type == "F":
                self.feed = cmd.value
        delta = newpos - self.pos
        self.actions.append(LinearMovement(delta, self.feed, self.acc))
        self.pos = newpos

    def __tobegin(self, cmds):
        x = False
        y = False
        z = False
        for cmd in cmds:
            if cmd.type == "X":
                x = True
            elif cmd.type == "Y":
                y = True
            elif cmd.type == "Z":
                z = True
        self.actions.append(ToBeginMovement(x, y, z))

    def __set_curaction(self, action):
        if self.curaction != self.__none:
            raise Exception ("Invalid command")
        self.curaction = action

    def set_acceleration(self, frame):
        for cmd in frame.commands:
            if cmd.type == "T":
                self.acc = cmd.value

    def __set_acc(self, cmds):
        acc = None
        for cmd in cmds:
            if cmd.type == "T":
                acc = cmd.value
        if acc != None:
            self.actions.append(SetAcceleration(acc))

    def process(self, frame):
        for cmd in frame.commands:
            if cmd.type == "G" and (cmd.value == 0 or cmd.value == 1):
                self.__set_curaction(self.__move)
            elif cmd.type == "G" and cmd.value == 90:
                self.relative = False
            elif cmd.type == "G" and cmd.value == 91:
                self.relative = True
            elif cmd.type == "G" and cmd.value == 28:
                self.__set_curaction(self.__tobegin)
            elif cmd.type == "M" and cmd.value == 204:
                self.set_acceleration(frame)
                self.__set_curaction(self.__set_acc)
        if self.curaction != None:
            self.curaction(frame.commands)
        self.curaction = self.__none

    def concat_moves(self):
        prevmove = None
        feed = 0
        d = euclid3.Vector3(0, 0, 0)
        moves = [action for action in self.actions if action.is_moving()]
        for move in moves:
            curf = move.feed
            md = move.dir0()
            k = md.x * d.x + md.y * d.y + md.z * d.z
            if k < 0:
                k = 0
            if k >= 1 - 1e-6:
                if feed < curf:
                    move.feed0 = feed
                    if prevmove != None:
                        prevmove.feed1 = feed
                else:
                    move.feed0 = curf
                    if prevmove != None:
                        prevmove.feed1 = curf

            feed = curf
            prevmove = move           
            d = move.dir1()
            

    def generate_control(self):
        for act in self.actions:
            self.outcode.append(act.make_code())
