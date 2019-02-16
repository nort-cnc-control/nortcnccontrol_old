#/usr/bin/env python3

import abc
import euclid3
import math

import traceback

from enum import Enum

from . import actions
from . import parser

from .actions import homing
from .actions import linear
from .actions import helix
from .actions import action
from .actions import pause
from .actions import tools
from .actions import spindle
from .actions import program

import common
from common import event
from common import config
import threading

# Supported codes
#
# G0/G1
# G2/G3
# G17/G18/G19
# G74
# G90
# G91
# G94
# M0
# M204

class Machine(object):

    class PositioningState(object):

        class CoordinateSystem(object):

            def __init__(self, x, y, z):
                self.x = x
                self.y = y
                self.z = z

            def local2global(self, x, y, z):
                return euclid3.Vector3(x + self.x, y + self.y, z + self.z)
            
            def global2local(self, x, y, z):
                return euclid3.Vector3(x - self.x, y - self.y, z - self.z)

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
            yz = 19
            zx = 18

        class PositioningGroup(Enum):
            absolute = 90
            relative = 91

        class FeedRateGroup(Enum):
            inverse_time = 93
            feed = 94
            feed_per_revolution = 95

        class UnitsGroup(Enum):
            inches = 20
            mms = 21

        class CutterRadiusCompenstationGroup(Enum):
            no_compensation = 40
            compensate_left = 41
            compensate_right = 42

        class ToolLengthOffsetGroup(Enum):
            compensation_negative = 43
            compensation_positive = 44
            no_compensation = 49

        class SpindleSpeedGroup(Enum):
            constant_surface_speed = 96
            rpm_speed = 97

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

        def __init__(self):
            self.feed = common.config.DEFAULT_FEED
            self.fastfeed = common.config.FASTFEED
            self.acc = common.config.ACCELERATION
            self.jerk = common.config.JERKING

            # global coordinates
            self.pos = euclid3.Vector3(0, 0, 0)

            self.motion       = self.MotionGroup.fast_move
            self.plane        = self.PlaneGroup.xy
            self.positioning  = self.PositioningGroup.absolute
            self.feed_mode    = self.FeedRateGroup.feed
            self.UnitsGroup   = self.UnitsGroup.mms
            self.CRC          = self.CutterRadiusCompenstationGroup.no_compensation
            self.TLO          = self.ToolLengthOffsetGroup.no_compensation
            self.Spindle      = self.SpindleSpeedGroup.rpm_speed
            self.canned       = self.CannedCyclesGroup.retract_origin
            self.coord_system = self.CoordinateSystemGroup.no_offset

            self.offsets = {
                self.CoordinateSystemGroup.no_offset : self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_1  : self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_2  : self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_3  : self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_4  : self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_5  : self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_6  : self.CoordinateSystem(0, 0, 0),
            }


        def process_frame(self, frame):
            for cmd in frame.commands:
                if cmd.type != "G":
                    continue
                if cmd.value == 0:
                    self.motion = self.MotionGroup.fast_move
                elif cmd.value == 1:
                    self.motion = self.MotionGroup.line
                if cmd.value == 2:
                    self.motion = self.MotionGroup.round_cw
                elif cmd.value == 3:
                    self.motion = self.MotionGroup.round_ccw
                elif cmd.value == 17:
                    self.plane = self.PlaneGroup.xy
                elif cmd.value == 19:
                    self.plane = self.PlaneGroup.yz
                elif cmd.value == 18:
                    self.plane = self.PlaneGroup.zx
                elif cmd.value == 53:
                    self.coord_system = self.CoordinateSystemGroup.no_offset
                elif cmd.value == 54:
                    self.coord_system = self.CoordinateSystemGroup.offset_1
                elif cmd.value == 55:
                    self.coord_system = self.CoordinateSystemGroup.offset_2
                elif cmd.value == 56:
                    self.coord_system = self.CoordinateSystemGroup.offset_3
                elif cmd.value == 57:
                    self.coord_system = self.CoordinateSystemGroup.offset_4
                elif cmd.value == 58:
                    self.coord_system = self.CoordinateSystemGroup.offset_5
                elif cmd.value == 59:
                    self.coord_system = self.CoordinateSystemGroup.offset_6
                elif cmd.value == 90:
                    self.positioning = self.PositioningGroup.absolute
                elif cmd.value == 91:
                    self.positioning = self.PositioningGroup.relative
                elif cmd.value == 94:
                    self.feed_mode = self.FeedRateGroup.feed

    class ToolState(object):

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
            self.tool         = 0
            self.speed        = 0

            self.spindle      = self.SpindleGroup.spindle_stop
            self.coolant      = self.CoolantGroup.no_coolant
            self.clamp        = self.ClampGroup.unclamp

        def process_begin(self, frame):
            for cmd in frame.commands:
                if cmd.type != "M":
                    continue
                if cmd.value == 3:
                    self.spindle = self.SpindleGroup.spindle_cw
                elif cmd.value == 4:
                    self.spindle = self.SpindleGroup.spindle_ccw
                elif cmd.value == 7:
                    self.coolant = self.CoolantGroup.coolant_2
                elif cmd.value == 8:
                    self.coolant = self.CoolantGroup.coolant_1
                elif cmd.value == 10:
                    self.clamp = self.ClampGroup.clamp
                elif cmd.value == 11:
                    self.clamp = self.ClampGroup.unclamp
                # TODO: other commands

        def process_end(self, frame):
            for cmd in frame.commands:
                if cmd.type != "M":
                    continue
                if cmd.value == 5:
                    self.spindle = self.SpindleGroup.spindle_stop
                elif cmd.value == 9:
                    self.coolant = self.CoolantGroup.no_coolant

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
            self.N = frame.commands[0].value

    class ExactStop(object):

        exact_stop = False

        def __init__(self, frame):
            for cmd in frame.commands:
                if cmd.type == "G" and cmd.value == 9:
                    self.exact_stop = True
                    break

    def __init__(self, table_sender, spindle_sender):
        print("Creating machine...")
        self.stop           = True
        self.table_sender   = table_sender
        self.spindle_sender = spindle_sender
        self.running        = event.EventEmitter()
        self.paused         = event.EventEmitter()
        self.finished       = event.EventEmitter()
        self.line_selected  = event.EventEmitter()
        self.tool_selected  = event.EventEmitter()
        self.init()
        print("done")

    def init(self):
        self.index = 0
        self.line_number = None
        self.actions = []
        self.table_state = self.PositioningState()
        self.tool_state = self.ToolState()
        self.work_init()

    def work_init(self):
        self.stop = True
        self.iter = 0
        self.display_paused = False
        for (_, action) in self.actions:
            action.completed.clear()
            action.ready.clear()
        if len(self.actions) > 0:
            self.line_selected(self.actions[0][0])

    def __add_action(self, index, action):
        action.action_started += self.__action_started
        self.actions.append((index, action))

    def __set_feed(self, feed):
        if self.table_state.feed_mode != self.PositioningState.FeedRateGroup.feed:
            raise Exception("Unsupported feed mode %s" % self.table_state.feed_mode)
        self.table_state.feed = feed

    def __set_acceleration(self, acc):
        self.table_state.acc = acc
    
    def __set_jerk(self, jerk):
        self.table_state.jerk = jerk

    #region Add MCU actions to queue

    #region movement
    def __insert_fast_movement(self, delta, exact_stop):
        movement = linear.LinearMovement(delta, feed=self.table_state.fastfeed,
                                         acc=self.table_state.acc,
                                         exact_stop=exact_stop,
                                         sender=self.table_sender)
        self.__add_action(self.index, movement)

    def __insert_movement(self, delta, exact_stop):
        movement = linear.LinearMovement(delta, feed=self.table_state.feed,
                                         acc=self.table_state.acc,
                                         exact_stop=exact_stop,
                                         sender=self.table_sender)
        self.__add_action(self.index, movement)

    def __axis_convert(self, axis):
        if axis == self.PositioningState.PlaneGroup.xy:
            axis = helix.HelixMovement.Axis.xy
        elif axis == self.PositioningState.PlaneGroup.yz:
            axis = helix.HelixMovement.Axis.yz
        else:
            axis = helix.HelixMovement.Axis.zx
        return axis

    def __insert_arc_R(self, delta, R, exact_stop):
        ccw = self.table_state.motion == self.PositioningState.MotionGroup.round_ccw
        axis = self.__axis_convert(self.table_state.plane)
        movement = helix.HelixMovement(delta, feed=self.table_state.feed, r=R,
                                       axis=axis, ccw=ccw,
                                       acc=self.table_state.acc,
                                       exact_stop=exact_stop,
                                       sender=self.table_sender)
        self.__add_action(self.index, movement)

    def __insert_arc_IJK(self, delta, I, J, K, exact_stop):
        ccw = self.table_state.motion == self.PositioningState.MotionGroup.round_ccw
        axis = self.__axis_convert(self.table_state.plane)
        movement = helix.HelixMovement(delta, feed=self.table_state.feed, i=I, j=J, k=K,
                                       axis=axis, ccw=ccw,
                                       acc=self.table_state.acc,
                                       exact_stop=exact_stop,
                                       sender=self.table_sender)
        self.__add_action(self.index, movement)

    def __insert_move(self, pos, exact_stop):

        print("*** Insert move ", pos.X, pos.Y, pos.Z)
        #traceback.print_stack()
        if self.table_state.positioning == self.PositioningState.PositioningGroup.absolute:
            cs = self.table_state.offsets[self.table_state.coord_system]

            origpos = self.table_state.pos
            origpos = cs.global2local(origpos.x, origpos.y, origpos.z)
            newpos = origpos

            if pos.X != None:
                newpos = euclid3.Vector3(pos.X, newpos.y, newpos.z)
            if pos.Y != None:
                newpos = euclid3.Vector3(newpos.x, pos.Y, newpos.z)
            if pos.Z != None:
                newpos = euclid3.Vector3(newpos.x, newpos.y, pos.Z)

            delta = newpos - origpos
        else:
            delta = euclid3.Vector3()
            if pos.X != None:
                delta.x = pos.X
            if pos.Y != None:
                delta.y = pos.Y
            if pos.Z != None:
                delta.z = pos.Z

        # Normal linear move
        if self.table_state.motion == self.PositioningState.MotionGroup.line:
            self.__insert_movement(delta, exact_stop)
        
        # Fast linear move
        elif self.table_state.motion == self.PositioningState.MotionGroup.fast_move:
            self.__insert_fast_movement(delta, exact_stop)
        
        # Arc movement
        elif self.table_state.motion == self.PositioningState.MotionGroup.round_cw or \
             self.table_state.motion == self.PositioningState.MotionGroup.round_ccw:
            if pos.R != None:
                self.__insert_arc_R(delta, pos.R, exact_stop)
            else:
                ci = 0
                cj = 0
                ck = 0
                if pos.I != None:
                    ci = pos.I
                if pos.J != None:
                    cj = pos.J
                if pos.K != None:
                    ck = pos.K
                self.__insert_arc_IJK(delta, ci, cj, ck, exact_stop)

        else:
            raise Exception("Not implemented %s motion state" % self.table_state.motion)

        self.table_state.pos += delta

    #endregion

    def __insert_homing(self, frame):
        self.__add_action(self.index, homing.ToBeginMovement(sender=self.table_sender))

    #endregion Add MCU actions to queue

    #region Spindle actions
    def __insert_set_speed(self, speed):
        self.tool_state.speed = speed
        self.__add_action(self.index, spindle.SpindleSetSpeed(self.spindle_sender, speed))
    
    def __insert_spindle_on(self, cw):
        if cw:
            self.tool_state.spindle = self.tool_state.spindle.spindle_cw
        else:
            self.tool_state.spindle = self.tool_state.spindle.spindle_ccw
        self.__add_action(self.index, spindle.SpindleOn(self.spindle_sender, self.tool_state.speed, cw))

    def __insert_spindle_off(self):
        self.tool_state.spindle = self.tool_state.spindle.spindle_stop
        self.__add_action(self.index, spindle.SpindleOff(self.spindle_sender))

    #endregion Tool actions

    #region Add UI action 

    #region pause
    def __paused(self):
        self.display_paused = True

    def __insert_pause(self):
        p = pause.WaitResume()
        p.paused += self.__paused
        self.__add_action(self.index, p)
    #endregion

    #region tool
    def __tool_selected(self, tool):
        self.tool_selected(tool)

    def __insert_select_tool(self, tool):
        self.tool_state.tool = tool
        tl = tools.WaitTool(tool)
        tl.tool_changed += self.__tool_selected
        self.__add_action(self.index, tl)
    #endregion

    #region Finish
    def __finish(self, action):
            self.stop = True

    def __program_end(self):
        act = program.Finish()
        act.finished += self.__finish
        self.__add_action(self.index, act)
    #endregion

    #endregion Add UI action
    
    #region Processing frame
    def __start_stop_spindle(self, old, new):
        if old != new:
            if new == self.tool_state.SpindleGroup.spindle_stop:
                self.__insert_spindle_off()
            elif new == self.tool_state.SpindleGroup.spindle_cw:
                self.__insert_spindle_on(True)
            elif new == self.tool_state.SpindleGroup.spindle_ccw:
                self.__insert_spindle_on(False)

    def __process_begin(self, frame):
        old_state = self.tool_state.spindle
        self.tool_state.process_begin(frame)
        new_state = self.tool_state.spindle

        speed = self.SpindleSpeed(frame)
        if speed.speed != None and speed.speed != self.tool_state.speed:
            self.__insert_set_speed(speed.speed)
        self.__start_stop_spindle(old_state, new_state)
        
    def __process_move(self, frame):
        self.table_state.process_frame(frame)
        pos = self.Positioning(frame)
        feed = self.Feed(frame)
        stop = self.ExactStop(frame)
        tool = self.Tool(frame)
        
        no_motion = False

        for cmd in frame.commands:
            if cmd.type == "G":
                if cmd.value == 74:
                    self.__insert_homing(frame)
                elif cmd.value == 92:
                    # set offset registers
                    self.__set_coordinates(x=pos.X, y=pos.Y, z=pos.Z)
                    no_motion = True

        if tool.tool != None:
            self.__insert_select_tool(tool.tool)

        if feed.feed != None:
            self.__set_feed(feed.feed)

        if pos.is_moving and not no_motion:
            self.__insert_move(pos, stop.exact_stop)

    def __process_end(self, frame):

        old_state = self.tool_state.spindle
        self.tool_state.process_end(frame)
        new_state = self.tool_state.spindle

        self.__start_stop_spindle(old_state, new_state)
        
        for cmd in frame.commands:
            if cmd.type != "M":
                continue
            if cmd.value == 0:
                self.__insert_pause()
            elif cmd.value == 2:
                self.__program_end()
            elif cmd.value == 30:
                self.__program_end()

    def __process(self, frame):
        self.line_number = self.LineNumber(frame)

        self.__process_begin(frame)
        self.__process_move(frame)
        self.__process_end(frame)

        self.index += 1
    #endregion

    def __optimize(self):
        prevmove = None
        prevfeed = 0
        prevdir = euclid3.Vector3(0, 0, 0)

        for (_, move) in self.actions:

            if move.is_moving() == False:
                prevmove = None
                continue

            curfeed = move.feed
            curdir = move.dir0()

            if prevmove != None and prevmove.exact_stop != True:
                cosa = curdir.x * prevdir.x + curdir.y * prevdir.y + curdir.z * prevdir.z
                if cosa > 0:
                    if cosa < 1 + 1e-4 and cosa >= 1:
                        cosa = 1
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
                        startfeed = min(startfeed, self.table_state.jerk / sina)
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

    def __action_started(self, action):
        for i in range(len(self.actions)):
            if self.actions[i][1] == action:
                break
        if i >= len(self.actions):
            return
        self.line_selected(self.actions[i][0])

    def Load(self, frames):
        self.init()
        for frame in frames:
            self.__process(frame)
        self.__optimize()

    def MakeHoming(self, x, y, z):
        if not self.stop:
            raise Exception("Machine should be stopped")
        self.stop = False
        act = actions.homing.ToBeginMovement(self.table_sender)
        act.run()
        act.completed.wait()
        self.stop = True

    def MakeProbeZ(self):
        if not self.stop:
            raise Exception("Machine should be stopped")
        self.stop = False
        act = actions.homing.ProbeMovement(self.table_sender)
        act.run()
        act.completed.wait()
        self.stop = True

    def WorkContinue(self):
        self.stop = False
        self.running()
        if len(self.actions) == 0:
            self.finished()
            return True
        action = None
        while self.iter < len(self.actions):
            action = self.actions[self.iter][1]
            if not action.caching:
                # we should wait until previous actions are ready
                for i in range(self.iter):
                    prevframe = self.actions[i][1]
                    print("waiting for previous frame: %i" % prevframe.Nid)
                    prevframe.ready.wait()
                print("previous frames are ready")

            self.table_sender.has_slots.wait()
            cont = action.run()
            self.iter += 1

            if not cont and not self.stop:
                if self.display_paused:
                    self.paused(self.display_paused)
                self.display_paused = False
                return False
        self.actions[-1][1].completed.wait()
        self.finished()
        self.stop = True
        return True

    def WorkStart(self):
        self.work_init()
        return self.WorkContinue()

    def Reset(self):
        for (_, act) in self.actions:
            act.dispose()
        self.actions = []
        self.work_init()

    def WorkStop(self):
        self.work_init()
        self.stop = True
        self.finished()

    def __set_coordinates(self, x, y, z):
        index = self.table_state.coord_system
        if index == self.table_state.CoordinateSystemGroup.no_offset:
            raise Exception("Can not set offset for global CS")

        offset = self.table_state.offsets[index]
        if x != None:
            x0 = self.table_state.pos.x - x
        else:
            x0 = offset.x

        if y != None:
            y0 = self.table_state.pos.y - y
        else:
            y0 = offset.y

        if z != None:
            z0 = self.table_state.pos.z - z
        else:
            z0 = offset.z

        cs = self.table_state.CoordinateSystem(x0, y0, z0)
        self.table_state.offsets[index] = cs
