#/usr/bin/env python3

import abc
import euclid3
import math

import traceback

from enum import Enum

from . import actions
from . import parser
from . import modals

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
        self.stop           = True
        self.table_sender   = table_sender
        self.spindle_sender = spindle_sender
        self.running        = event.EventEmitter()
        self.paused         = event.EventEmitter()
        self.finished       = event.EventEmitter()
        self.line_selected  = event.EventEmitter()
        self.tool_selected  = event.EventEmitter()
        self.program = None
        self.reset = False
        self.action_rdy = threading.Event()
        self.work_init()
        print("done")

    def work_init(self):
        self.stop = True
        self.iter = 0
        self.reset = False
        self.display_paused = False
        if self.program:
            for (_, action, _) in self.program.actions:
                action.completed.clear()
                action.ready.clear()
        
    #region Add UI action 

    def __paused(self):
        self.display_paused = True

    def __tool_selected(self, tool):
        self.tool_selected(tool)

    def __finished(self, action):
        self.stop = True
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
        self.program = builder.build_program(frames)
        Optimizer.optimize(self.program, config.JERKING)
        for action in self.program.actions:
            action[1].action_started += self.__action_started
        if len(self.program.actions) > 0:
            self.line_selected(self.program.actions[0][2])


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

    def __has_cmds(self):
        return self.iter < len(self.program.actions)

    def __send_cached_commands(self):
        actions = []
        while self.__has_cmds() and self.table_sender.has_slots.is_set():
            action = self.program.actions[self.iter][1]
            if not action.caching:
                return actions, True
            actions.append(action)
            cont = action.run()
            self.iter += 1
            if not cont:
                return actions, False
        return actions, True

    def __process_block(self):
        actions, cont = self.__send_cached_commands()
        if not cont:
            return actions, None, False

        if self.__has_cmds():
            action = self.program.actions[self.iter][1]
            if action.caching:
                return actions, None, True

            self.iter += 1
            return actions, action, True
        
        return actions, None, True

    def WorkContinue(self):
        self.stop = False
        self.running()
        if self.program is None or len(self.program.actions) == 0:
            self.__finished(None)
            return

        lastaction = None
        while self.__has_cmds() and not self.stop:
            actions, ncaction, cont = self.__process_block()
            for action in actions:
                if self.reset:
                    self.reset = False
                    return
                if action.caching and not action.dropped:
                    lastaction = action

            if lastaction is not None and ncaction is not None:
                print("Waiting for table action %i" % lastaction.Nid)
                lastaction.ready.wait()
                print("Table action %i ready" % lastaction.Nid)

            if ncaction is not None and cont:
                cont = ncaction.run()
                if cont:
                    ncaction.ready.wait()

            if not cont:
                if not self.stop:
                    if self.display_paused:
                        self.paused(self.display_paused)
                        self.display_paused = False
                print("Exit")
                break
        if lastaction is not None and ncaction is not None:
            print("Waiting for table action %i" % lastaction.Nid)
            lastaction.ready.wait()
            print("Table action %i ready" % lastaction.Nid)

    def WorkStart(self):
        if not self.stop:
            raise Exception("Machine should be stopped")
        self.work_init()
        return self.WorkContinue()

    def Reset(self):
        print("RESET")
        self.reset = True
        self.work_init()

    def WorkStop(self):
        self.work_init()
        self.stop = True
        self.finished()
