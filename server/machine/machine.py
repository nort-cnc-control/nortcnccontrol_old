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
        self.is_running        = False
        self.is_finished    = False
        self.table_sender   = table_sender
        self.spindle_sender = spindle_sender
        self.running        = event.EventEmitter()
        self.paused         = event.EventEmitter()
        self.finished       = event.EventEmitter()
        self.line_selected  = event.EventEmitter()
        self.tool_selected  = event.EventEmitter()
        self.lastaction = None
        self.reset = False
        self.action_rdy = threading.Event()
        # loaded program
        self.user_program = None
        # actual program
        self.program = None
        # special programs
        self.z_probe_program = pr.Program(self.table_sender, self.spindle_sender)
        self.z_probe_program.insert_z_probe()
        self.homing_program = pr.Program(self.table_sender, self.spindle_sender)
        self.homing_program.insert_homing()
        self.work_init()
        print("done")

    def work_init(self):
        print("INIT")
        self.is_running = False
        self.iter = 0
        self.reset = False
        self.display_paused = False
        self.lastaction = None
        if self.program:
            for (_, action, _) in self.program.actions:
                action.completed.clear()
                action.finished.clear()

    #region Add UI action 

    def __paused(self):
        self.display_paused = True
        self.paused("Press continue")

    def __tool_selected(self, tool):
        self.tool_selected(tool)

    def __finished(self, action):
        self.is_running = False
        self.is_finished = True
        self.finished()

    def __action_started(self, action):
        for i in range(len(self.program.actions)):
            if self.program.actions[i][1] == action:
                break
        if i >= len(self.program.actions):
            return
        self.line_selected(self.program.actions[i][2])

    def Load(self, frames):
        builder = ProgramBuilder(self.table_sender, self.spindle_sender)
        builder.finish_cb = self.__finished
        builder.pause_cb = self.__paused
        builder.tool_select_cb = self.__tool_selected
        self.user_program = builder.build_program(frames)
        Optimizer.optimize(self.user_program, config.JERKING)
        for action in self.user_program.actions:
            action[1].action_started += self.__action_started
        if len(self.user_program.actions) > 0:
            self.line_selected(self.user_program.actions[0][2])

    def MakeHoming(self, x, y, z):
        if self.is_running:
            raise Exception("Machine should be stopped")
        self.program = self.homing_program
        self.work_init()
        self.WorkContinue()

    def MakeProbeZ(self):
        if self.is_running:
            raise Exception("Machine should be stopped")
        self.program = self.z_probe_program
        self.work_init()
        self.WorkContinue()

    def __has_cmds(self):
        return self.iter < len(self.program.actions)

    def __get_cacheable(self):
        actions = []
        while self.__has_cmds():
            action = self.program.actions[self.iter][1]
            if not action.caching:
                return actions
            actions.append(action)
            self.iter += 1
        return actions
        
    def __get_action(self):
        if not self.__has_cmds():
            return None
        action = self.program.actions[self.iter][1]
        self.iter += 1
        return action

    class StateMachine(Enum):
        WorkContinue = 1
        ProcessBlock = 2
        WaitSlots = 3
        SendCacheable = 4
        WaitCacheable = 5
        ProcessNotCacheable = 6
        RunNotCacheable = 7
        WaitNotCacheable = 8
        Interrupt = 9
        End = 10
        Reseted = 11
        WaitCommand = 12

    def WorkContinue(self):
        self.reset = False
        self.is_running = True
        self.is_finished = False
        self.running()

        state = self.StateMachine.WorkContinue
        actions = []
        action = None

        while True:
            print("State = ", state)
            if state is self.StateMachine.WorkContinue:
                if not self.__has_cmds():        
                    state = self.StateMachine.End
                else:
                    state = self.StateMachine.ProcessBlock
                    continue
            elif state is self.StateMachine.End:
                if not self.is_finished:
                    self.finished()
                break
            elif state is self.StateMachine.Reseted:
                self.reset = True
                break
            elif state is self.StateMachine.WaitCommand:
                break
            elif state is self.StateMachine.ProcessBlock:
                actions = self.__get_cacheable()
                if len(actions) > 0:
                    self.lastaction = None
                    state = self.StateMachine.WaitSlots
                else:
                    state = self.StateMachine.ProcessNotCacheable
            elif state is self.StateMachine.ProcessNotCacheable:
                action = self.__get_action()
                if action.is_pause is True:
                    state = self.StateMachine.Interrupt
                else:
                    state = self.StateMachine.RunNotCacheable
                continue
            elif state is self.StateMachine.WaitSlots:
                self.table_sender.has_slots.wait()
                if self.reset:
                    state = self.StateMachine.Reseted
                else:
                    state = self.StateMachine.SendCacheable
                continue
            elif state is self.StateMachine.SendCacheable:
                action = actions[0]
                action.run()
                if self.reset:
                    state = self.StateMachine.Reseted
                else:
                    if not action.dropped:
                        self.lastaction = action
                    actions = actions[1:]
                    if len(actions) > 0:
                        state = self.StateMachine.WaitSlots
                    else:
                        state = self.StateMachine.WaitCacheable
                continue
            elif state is self.StateMachine.WaitCacheable:
                if self.lastaction is not None:
                    self.lastaction.finished.wait()
                
                if self.reset:
                    state = self.StateMachine.Reseted
                elif not self.__has_cmds():
                    state = self.StateMachine.End
                else:
                    state = self.StateMachine.ProcessNotCacheable
                continue
            elif state is self.StateMachine.RunNotCacheable:
                action.run()
                state = self.StateMachine.WaitNotCacheable
                continue
            elif state is self.StateMachine.WaitNotCacheable:
                action.finished.wait()
                if self.reset:
                    state = self.StateMachine.Reseted
                elif self.__has_cmds():
                    state = self.StateMachine.ProcessBlock
                else:
                    state = self.StateMachine.End
                continue
            elif state is self.StateMachine.Interrupt:
                action.run()
                if self.is_finished:
                    state = self.StateMachine.End
                else:
                    state = self.StateMachine.WaitCommand
                continue
        self.is_running = False

    def WorkStart(self):
        if self.is_running:
            raise Exception("Machine should be stopped")
        self.program = self.user_program
        
        if self.program is None:
            self.__finished(None)
            return
        self.work_init()
        return self.WorkContinue()

    def Reset(self):
        print("RESET")
        act = system.TableReset(sender=self.table_sender)
        act.run()
        self.reset = True
        if self.lastaction is not None:
            self.lastaction.abort()
        self.table_sender.reset()
        self.spindle_sender.stop()
        self.work_init()

    def WorkStop(self):
        self.work_init()
        self.is_running = False
        self.finished()
