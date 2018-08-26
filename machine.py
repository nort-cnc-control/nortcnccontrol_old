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

    class MachineState(object):

        class MotionGroup(Enum):
            fast_move = 0
            line = 1
            round_cw = 2
            round_ccw = 3
            parabolic = 6
            threading = 33
            treading_inc = 34
            threading_dec = 35

        class PlaneGroup(Enum):
            xy = 17
            yz = 18
            zx = 19

        class PositioningGroup(Enum):
            absolute = 90
            relative = 91

        class FeedRateGroup(Enum):
            inverse_time = 93
            feed = 94
            feed_per_round = 95

        class UnitsGroup(Enum):
            inches = 20
            mms = 21

        class CutterRadiusCompenstationGroup(Enum):
            no_compensation = 40
            compensate_left = 41
            compensate_right = 42

        class ToolLengthOffset(Enum):
            compensation_negative = 43
            compensation_positive = 44
            no_compensation = 49

        class CannedCyclesGroup(Enum):
            retract_origin = 98
            retract_r = 99

        class CoordinateSystemGroup(Enum):
            no_offset = 53
            offset_1  = 54
            offset_2  = 55
            offset_3  = 56
            offset_4  = 57
            offset_5  = 58
            offset_6  = 59

        class SpindleGroup(Enum):
            spindle_cw = 3
            spindle_ccw = 4
            spindle_stop = 5
        
        class CoolantGroup(Enum):
            coolant_1 = 7
            coolant_2 = 8
            no_coolant = 9
        
        class ClampGroup(Enum):
            clamp = 10
            unclamp = 11
        
        def __init__(self):
            self.feed = 5
            self.fastfeed = 1200
            self.acc = 1000
            self.jerk = 20
            self.pos = euclid3.Vector3()

            self.motion       = self.MotionGroup.fast_move
            self.plane        = self.PlaneGroup.xy
            self.positioning  = self.PositioningGroup.absolute
            self.feed_mode    = self.FeedRateGroup.feed
            self.UnitsGroup   = self.UnitsGroup.mms
            self.CRC          = self.CutterRadiusCompenstationGroup.no_compensation
            self.TLO          = self.ToolLengthOffset.no_compensation
            self.canned       = self.CannedCyclesGroup.retract_origin
            self.coord_system = self.CoordinateSystemGroup.no_offset

        def process_frame(self, frame):
            for cmd in frame.commands:
                if cmd.type == "G":
                    if cmd.value == 0:
                        self.motion = self.MotionGroup.fast_move
                    elif cmd.value == 1:
                        self.motion = self.MotionGroup.line
                    elif cmd.value == 90:
                        self.positioning = self.PositioningGroup.absolute
                    elif cmd.value == 91:
                        self.positioning = self.PositioningGroup.relative
                    elif cmd.value == 94:
                        self.feed_mode = self.FeedRateGroup.feed

    class Positioning(object):

        moving = False
        X = None
        Y = None
        Z = None

        def __init__(self, frame):
            for cmd in frame.commands:
                if cmd.type == "X":
                    if self.X != None:
                        raise Exception("X meets 2 times")
                    self.X = cmd.value
                    self.moving = True
                elif cmd.type == "Y":
                    if self.Y != None:
                        raise Exception("Y meets 2 times")
                    self.Y = cmd.value
                    self.moving = True
                elif cmd.type == "Z":
                    if self.Z != None:
                        raise Exception("Z meets 2 times")
                    self.Z = cmd.value
                    self.moving = True

    class Feed(object):

        F = None
        
        def __init__(self, frame):
            for cmd in frame.commands:
                if cmd.type == "F":
                    if self.F != None:
                        raise Exception("F meets 2 times")
                    self.F = cmd.value
        

    actions = []
    
    relative = False

    def __init__(self):
        self.state = self.MachineState()

    def __set_feed(self, feed):
        if self.state.feed_mode != self.MachineState.FeedRateGroup.feed:
            raise Exception("Unsupported feed mode %s" % self.state.feed_mode)
        self.state.feed = feed

    def __set_acceleration(self, acc):
        self.state.acc = acc
    
    def __set_jerk(self, jerk):
        self.state.jerk = jerk

    def __insert_move(self, pos):
        newpos = self.state.pos

        if self.state.positioning == self.MachineState.PositioningGroup.relative:
            if pos.X != None:
                newpos = euclid3.Vector3(pos.X + newpos.x, newpos.y, newpos.z)
            if pos.Y != None:
                newpos = euclid3.Vector3(newpos.x, pos.Y + newpos.y, newpos.z)
            if pos.Z != None:
                newpos = euclid3.Vector3(newpos.x, newpos.y, pos.Z + newpos.z)
        elif self.state.positioning == self.MachineState.PositioningGroup.absolute:
            if pos.X != None:
                newpos = euclid3.Vector3(pos.X, newpos.y, newpos.z)
            if pos.Y != None:
                newpos = euclid3.Vector3(newpos.x, pos.Y, newpos.z)
            if pos.Z != None:
                newpos = euclid3.Vector3(newpos.x, newpos.y, pos.Z)

        delta = newpos - self.state.pos

        if self.state.motion == self.MachineState.MotionGroup.line:
            feed = self.state.feed
        elif self.state.motion == self.MachineState.MotionGroup.fast_move:
            feed = self.state.fastfeed
        else:
            raise Exception("Not implemented %s motion state" % self.state.motion)

        self.actions.append(linear.LinearMovement(delta, feed, self.state.acc))
        self.state.pos = newpos

    def __insert_homing(self, frame):
        self.actions.append(homing.ToBeginMovement())

    def __insert_pause(self):
        self.actions.append(pause.WaitResume())

    def __process(self, frame):

        self.state.process_frame(frame)
        pos = self.Positioning(frame)
        feed = self.Feed(frame)

        if feed.F != None:
            self.__set_feed(feed.F)

        if pos.moving:
            self.__insert_move(pos)

        for cmd in frame.commands:
            if cmd.type == "G":
                # Not modal commands
                if cmd.value == 28:
                    self.__insert_homing(frame)

            elif cmd.type == "M":
                if cmd.value == 0:
                    self.__insert_pause()
                else:
                    raise Exception("Unsupported command M%i" % cmd.value)


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
                        startfeed = min(startfeed, self.state.jerk / sina)
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
        self.__optimize()

    def run(self):
        for a in self.actions:
            a.act()
