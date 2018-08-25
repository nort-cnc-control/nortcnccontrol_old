#/usr/bin/env python3

import abc
import euclid3
import math

from enum import Enum

import homing
import linear
import action
import pause

# Supported codes
#
# G0/G1
# G28
# G90
# G91
# G94
# M0
# M204

class Machine(object):

    class MachineState(Enum):
        idle = 0
        moving = 1
        pause = 2

    outcode = []
    actions = []
    feed = 5
    fastfeed = 1200
    acc = 1000
    jerk = 2000
    pos = euclid3.Vector3()
    relative = False

    def __init__(self):
        self.state = self.MachineState.idle

    def __set_feed(self, frame):
        for cmd in frame.commands:
            if cmd.type == "F":
                self.feed = cmd.value

    def __set_acceleration(self, frame):
        for cmd in frame.commands:
            if cmd.type == "T":
                self.acc = cmd.value
            elif cmd.type == "F":
                self.jerk = cmd.value

    def __insert_move(self, frame):
        newpos = self.pos
        fast = False
        for cmd in frame.commands:
            if cmd.type == "G" and cmd.value == 0:
                fast = True
        if self.relative:
            for cmd in frame.commands:
                if cmd.type == "X":
                    newpos = euclid3.Vector3(cmd.value + newpos.x, newpos.y, newpos.z)
                elif cmd.type == "Y":
                    newpos = euclid3.Vector3(newpos.x, cmd.value + newpos.y, newpos.z)
                elif cmd.type == "Z":
                    newpos = euclid3.Vector3(newpos.x, newpos.y, cmd.value + newpos.z)
        else:
            for cmd in frame.commands:
                if cmd.type == "X":
                    newpos = euclid3.Vector3(cmd.value, newpos.y, newpos.z)
                elif cmd.type == "Y":
                    newpos = euclid3.Vector3(newpos.x, cmd.value, newpos.z)
                elif cmd.type == "Z":
                    newpos = euclid3.Vector3(newpos.x, newpos.y, cmd.value)
        for cmd in frame.commands:
            if cmd.type == "F":
                self.feed = cmd.value
        delta = newpos - self.pos
        if not fast:
            self.actions.append(linear.LinearMovement(delta, self.feed, self.acc))
        else:
            self.actions.append(linear.LinearMovement(delta, self.fastfeed, self.acc))
        self.pos = newpos

    def __insert_tobegin(self, frame):
        x = False
        y = False
        z = False
        for cmd in frame.commands:
            if cmd.type == "X":
                x = True
            elif cmd.type == "Y":
                y = True
            elif cmd.type == "Z":
                z = True
        self.actions.append(homing.ToBeginMovement(x, y, z))

    def __insert_pause(self):
        self.actions.append(pause.WaitResume())

    def __process(self, frame):
        for cmd in frame.commands:
            if cmd.type == "G":
                if cmd.value == 0 or cmd.value == 1:
                    self.__insert_move(frame)
                elif cmd.value == 28:
                    self.__insert_tobegin(frame)
                elif cmd.value == 90:
                    self.relative = False
                elif cmd.value == 91:
                    self.relative = True
                elif cmd.value == 94:
                    self.__set_feed(frame)
            elif cmd.type == "M":
                if cmd.value == 0:
                    self.__insert_pause()
                elif cmd.value == 204:
                    self.__set_acceleration(frame)

    def __optimize(self):
        prevmove = None
        prevfeed = 0
        prevdir = euclid3.Vector3(0, 0, 0)

        for move in self.actions:
            curfeed = move.feed
            curdir = move.dir0()

            if move.is_moving() == False:
                prevmove = None
                continue

            if prevmove != None:
                cosa = curdir.x * prevdir.x + curdir.y * prevdir.y + curdir.z * prevdir.z
                if cosa > 0:
                    sina = math.sqrt(1-cosa**2)
                    if sina < 1e-3:
                        # The same direction
                        #
                        # startfeed = prevfeed
                        # endfeed <= prevfeed
                        # startfeed <= curfeed

                        startfeed = min(curfeed, prevfeed)
                        endfeed = startfeed
                        move.feed0 = startfeed
                        prevmove.feed1 = endfeed
                    else:
                        # Have direction change
                        #
                        # endfeed = startfeed * cosa
                        # startfeed * sina <= jump
                        # endfeed <= prevfeed
                        # startfeed <= curfeed

                        startfeed = curfeed
                        startfeed = min(startfeed, prevfeed / cosa)
                        startfeed = min(startfeed, self.jerk / sina)
                        endfeed = startfeed * cosa

                        move.feed0 = startfeed
                        prevmove.feed1 = endfeed
                else:
                    # Change direction more than 90
                    #
                    # endfeed = 0
                    # startfeed = 0
                    prevmove.feed1 = 0
                    move.feed0 = 0
            else:
                # first move
                move.feed0 = 0

            prevfeed = curfeed
            prevmove = move           
            prevdir = move.dir1()

    def load(self, frames):
        for frame in frames:
            self.__process(frame)

    def run(self):
        for a in self.actions:
            a.act()
