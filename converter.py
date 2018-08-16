#/usr/bin/env python3

import abc
import euclid3
import math

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
        g1 = "G01 F%i P%i L%i " % (self.feed+0.5, self.feed0+0.5, self.feed1+0.5)
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
    acc = 1000
    jump = 2000
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
            elif cmd.type == "F":
                self.jump = cmd.value

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
        prevfeed = 0
        prevdir = euclid3.Vector3(0, 0, 0)
        moves = [action for action in self.actions if action.is_moving()]
        for move in moves:
            curfeed = move.feed
            curdir = move.dir0()
            cosa = curdir.x * prevdir.x + curdir.y * prevdir.y + curdir.z * prevdir.z
            if cosa > 0:
                sina = math.sqrt(1-cosa**2)
                if sina < 1e-3:
                    # Mostly same direction
                    if prevfeed < curfeed:
                        move.feed0 = prevfeed
                        if prevmove != None:
                            prevmove.feed1 = prevfeed
                    else:
                        move.feed0 = curfeed
                        if prevmove != None:
                            prevmove.feed1 = curfeed
                else:
                    # Have direction change
                    #
                    # endfeed = startfeed * cosa
                    # startfeed * sina <= jump
                    # endfeed <= prevfeed
                    # startfeed <= curfeed

                    startfeed = curfeed

                    startfeed = min(startfeed, self.jump / sina)
                    if cosa > 0:
                        startfeed = min(startfeed, prevfeed / cosa)
                    endfeed = startfeed * cosa

                    move.feed0 = startfeed
                    prevmove.feed1 = endfeed
            else:
                # Change direction
                if prevmove != None:
                    prevmove.feed1 = 0
                move.feed0 = 0

            prevfeed = curfeed
            prevmove = move           
            prevdir = move.dir1()
            

    def generate_control(self):
        for act in self.actions:
            self.outcode.append(act.make_code())
