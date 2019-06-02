#/usr/bin/env python3

import abc
import euclid3
import math

import traceback

from enum import Enum

from . import actions
from . import parser
from . import modals
from . import program as pr

from .actions import linear
from .actions import helix
from .actions import action
from .actions import pause
from .actions import tools
from .actions import spindle
from .actions import program
from .actions import system

import common
from common import event
from common import config
import threading

from .program_builder import ProgramBuilder
from .modals import positioning
from .modals import tool
from .optimizer import Optimizer
from . import arguments

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
# M97
# M99
# M204

class Machine(object):

    def __init__(self, table_sender, spindle_sender):
        print("Creating machine...")
        self.registers = {
            "tools" : {}
        }
        self.is_running     = False
        self.is_finished    = False
        self.table_sender   = table_sender
        self.spindle_sender = spindle_sender
        self.running        = event.EventEmitter()
        self.paused         = event.EventEmitter()
        self.finished       = event.EventEmitter()
        self.error          = event.EventEmitter()
        self.line_selected  = event.EventEmitter()
        self.tool_selected  = event.EventEmitter()
        self.reset = False
        self.action_rdy = threading.Event()
        self.__table_reseted_ev = threading.Event()
        self.current_wait = None
        self.c_actions = []
        self.nc_action = None
        self.opt = Optimizer(common.config.JERKING, common.config.ACCELERATION, common.config.MAXFEED)
        # loaded program
        self.user_program = None
        self.user_frames = []
        # actual program
        self.program = None
        self.state = None
        self.builder = None
        # special programs
        self.empty_program = pr.Program(self.table_sender, self.spindle_sender)
        # states
        self.previous_state = None
        self.work_init(self.empty_program)
        self.table_sender.mcu_reseted += self.__table_reseted
        print("done")

    def work_init(self, program):
        print("INIT")
        self.program = program
        self.is_running = False
        self.iter = 0
        self.reset = False
        self.display_paused = False
        self.display_finished = True
        for (_, action, _, _) in self.program.actions:
            action.completed.clear()
            action.finished.clear()
            action.error = False
            action.crc_error = False
            action.is_received = False

    #region Add UI action 

    def __paused(self):
        self.display_paused = True
        self.paused("Press continue")

    def __tool_selected(self, tool):
        self.tool_selected(tool)

    def __finished(self, action):
        if self.is_finished:
            return
        self.is_running = False
        self.is_finished = True
        self.finished(self.display_finished)
        if self.builder is not None:
            self.state = self.builder.get_state()
            #print("Offsets: ")
            #for off in self.state[0].offsets:
            #    val = self.state[0].offsets[off]
            #    print(off, "=", val.x, val.y, val.z)
        else:
            self.state = None
        if self.program is not self.user_program and self.program is not self.empty_program:
            self.program.dispose()
            self.program = self.empty_program

    def __action_started(self, action):
        i = None
        for i in range(len(self.program.actions)):
            if self.program.actions[i][1] == action:
                break
        if i is None or i >= len(self.program.actions):
            return
        self.line_selected(self.program.actions[i][2])

    def __build_user_program(self, frames):
        self.builder = ProgramBuilder(self.table_sender, self.spindle_sender, self.registers, self.state)
        self.builder.finish_cb = self.__finished
        self.builder.pause_cb = self.__paused
        self.builder.tool_select_cb = self.__tool_selected
        self.user_program = self.builder.build_program(frames)
        self.opt.optimize(self.user_program)
        for action in self.user_program.actions:
            action[1].action_started += self.__action_started
        if len(self.user_program.actions) > 0:
            self.line_selected(self.user_program.actions[0][2])

    def Load(self, frames):
        if self.user_program is not None:
            self.user_program.dispose()
        self.user_frames = frames

    def Execute(self, frame):
        if self.is_running:
            raise Exception("Machine should be stopped")

        self.builder = ProgramBuilder(self.table_sender, self.spindle_sender, self.registers, self.state)
        self.builder.finish_cb = self.__finished
        self.builder.pause_cb = self.__paused
        self.builder.tool_select_cb = self.__tool_selected
        
        self.work_init(self.builder.build_program([frame]))
        self.display_finished = False
        self.WorkContinue()

    def __has_cmds(self):
        return self.iter < len(self.program.actions)

    def __get_movements(self):
        actions = []
        while self.__has_cmds():
            action = self.program.actions[self.iter][1]
            if not action.caching:
                return actions
            actions.append(action)
            self.iter += 1
        return actions

    def __get_nc_action(self):
        if not self.__has_cmds():
            return None
        action = self.program.actions[self.iter][1]
        if action.caching:
            return None
        self.iter += 1
        return action

    def WorkReset(self):
        print("RESET")
        act = system.TableReset(sender=self.table_sender)
        act.run()
        self.reset = True

        self.table_sender.reset()
        self.spindle_sender.stop()
        self.state = None
        self.builder = None
        if self.program is not self.user_program and self.program is not self.empty_program:
            self.program.dispose()
            self.program = self.empty_program
    
    def __abort_actions(self):
        for action in self.c_actions:
            action.abort()
        if self.nc_action is not None:
            self.nc_action.abort()

    def __wait_event(self, ev):
        self.current_wait = ev
        self.current_wait.wait()

        if self.reset:
            self.__abort_actions()
            return True
        return False

    def __table_reseted(self):
        self.sm_state = self.StateMachine.Idle
        self.reset = True
        if self.current_wait is not None:
            self.current_wait.set()

        self.table_sender.reset()
        self.__abort_actions()
        self.spindle_sender.stop()
        self.__table_reseted_ev.set()

    class StateMachine(Enum):
        Idle = 0
        BlockStart = 1

        ProcessSegment = 2

        WaitSlots = 3
        SendMovement = 4
        WaitMCUAnswer = 5
        WaitMovements = 6

        ExecuteNotCacheable = 7
        WaitNotCacheable = 8

        Reset = 9
        ProgramInterrupted = 11

        BlockFinished = 12
        ProgramFinished = 13

    #   Program Start
    #          |               ---------------->------------------
    #          v               |                                 |
    #  -- Block Start -> Process Segment ----                    |       Reset command
    #  |     ^            ^    |            |                    |              |
    #  |     |            |    |            v                    |              v
    #  |     |     --------    |       Wait Slots  <--------     |          Send Reset CMD to MCU
    #  |     |     |           |            |              |     |              |
    #  |     |     |           |            v              |     |              v
    #  |     |     |           |    Send movement to MCU   |     |      Receive Reset from MCU <---- MCU hardware reset
    #  |     |     |           |            |   ^          |     |              |
    #  |     |     |           |            |   |          |     |              |
    #  |     |     |           |       Wait answer ---------     |              |
    #  |     |     |           |            |                    |              |
    #  |     |     |           |            |                    |              |
    #  |     |     |           |            v                    |              v
    #  |     |     |           |       Wait last movement        |         Stop spindel
    #  |     |     |           |          |     |                |              |
    #  |   Get Cmd |           |          |     |                |              v
    #  |     ^     |           v          |     |                |         Emergency state
    #  |     |     |    Run NC action <----     |                |
    #  |     |     |           |                |                |
    #  |     |     |           v                |                |
    #  |     |     ------ Wait NC action        |                |
    #  |     |               |     |            |                |
    #  |     |               |     |            |                |
    #  |  Block Finished <----     |            |                |
    #  |     |                     |            |                |
    #  |     v                     |            |                |
    #  --> Program Finished <-------------------------------------
    #
    def WorkContinue(self):
        self.reset = False
        self.is_running = True
        self.is_finished = False
        self.running()

        self.sm_state = self.StateMachine.BlockStart
        
        self.c_actions = []
        self.action = None
        self.last_c_action = None
        self.nc_action = None
        self.current_wait = None

        while True:
            print("State = ", self.sm_state)
            if self.sm_state is self.StateMachine.BlockStart:
                if not self.__has_cmds():
                    self.sm_state = self.StateMachine.ProgramFinished
                else:
                    self.sm_state = self.StateMachine.ProcessSegment
                continue
            elif self.sm_state is self.StateMachine.ProgramFinished:
                self.__finished(None)
                break
            elif self.sm_state is self.StateMachine.BlockFinished:
                break

            # Segment = (cacheable actions)*n [not cacheable action]
            elif self.sm_state is self.StateMachine.ProcessSegment:
                self.c_actions = self.__get_movements()
                self.nc_action = self.__get_nc_action()
                if len(self.c_actions) > 0:
                    self.sm_state = self.StateMachine.WaitSlots
                    self.last_c_action = None
                elif self.nc_action is not None:
                    self.sm_state = self.StateMachine.ExecuteNotCacheable
                else:
                    self.sm_state = self.StateMachine.ProgramFinished
                continue

            # Table movements
            elif self.sm_state is self.StateMachine.WaitSlots:
                if self.__wait_event(self.table_sender.has_slots):
                    self.sm_state = self.StateMachine.Reset
                    continue
                self.sm_state = self.StateMachine.SendMovement
                continue
            elif self.sm_state is self.StateMachine.SendMovement:
                self.action = self.c_actions[0]
                self.action.run()
                self.sm_state = self.StateMachine.WaitMCUAnswer
                continue
            elif self.sm_state == self.StateMachine.WaitMCUAnswer:
                if self.__wait_event(self.action.command_received):
                    self.sm_state = self.StateMachine.Reset
                    continue
                if self.action.crc_error:
                    self.sm_state = self.StateMachine.SendMovement
                    continue
                if self.action.error:
                    self.sm_state = self.StateMachine.Idle
                    self.error()
                    break
                if not self.action.dropped:
                    self.last_c_action = self.action
                self.c_actions = self.c_actions[1:]
                if len(self.c_actions) > 0:
                    self.sm_state = self.StateMachine.WaitSlots
                else:
                    self.sm_state = self.StateMachine.WaitMovements
                continue
            elif self.sm_state is self.StateMachine.WaitMovements:
                if self.last_c_action is not None:
                    if self.__wait_event(self.last_c_action.finished):
                        self.sm_state = self.StateMachine.Reset
                        continue

                if self.nc_action is None:
                    self.sm_state = self.StateMachine.ProgramFinished
                else:
                    self.sm_state = self.StateMachine.ExecuteNotCacheable
                
                self.last_c_action = None
                continue

            # Not cacheable actions
            elif self.sm_state is self.StateMachine.ExecuteNotCacheable:
                self.nc_action.run()
                self.sm_state = self.StateMachine.WaitNotCacheable
                continue
            elif self.sm_state is self.StateMachine.WaitNotCacheable:
                if self.__wait_event(self.nc_action.finished):
                    self.sm_state = self.StateMachine.Reset
                    continue
                if self.nc_action.is_pause is True:
                    self.sm_state = self.StateMachine.BlockFinished
                elif self.__has_cmds():
                    self.sm_state = self.StateMachine.ProcessSegment
                else:
                    self.sm_state = self.StateMachine.ProgramFinished
                self.nc_action = None
                continue

            # Reset
            elif self.sm_state is self.StateMachine.Reset:
                act = system.TableReset(sender=self.table_sender)
                act.run()
                self.__table_reseted_ev.wait()
                self.__finished(None)
                break

        self.is_running = False

    def WorkStart(self):
        if self.is_running:
            raise Exception("Machine should be stopped")
        self.__build_user_program(self.user_frames)
        if self.user_program is None:
            self.work_init(self.empty_program)  
        else:
            self.work_init(self.user_program)
        return self.WorkContinue()

    def WorkStop(self):
        self.work_init(self.empty_program)
        self.is_running = False
        self.__finished(None)

    def RegisterTool(self, tool, radius):
        self.registers["tools"][tool] = radius
