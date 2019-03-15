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
        self.work_init()
        print("done")

    def work_init(self):
        self.stop = True
        self.iter = 0
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

    def WorkContinue(self):
        self.stop = False
        self.running()
        if self.program is None or len(self.program.actions) == 0:
            self.finished()
            return True
        action = None
        while self.iter < len(self.program.actions) and not self.stop:
            action = self.program.actions[self.iter][1]
            if not action.caching:
                # we should wait until previous actions are ready
                for i in range(self.iter):
                    prevframe = self.program.actions[i][1]
                    #print("waiting for previous frame: %i" % prevframe.Nid)
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
        action.completed.wait()
        if not self.stop:
            self.finished()
        return True

    def WorkStart(self):
        if not self.stop:
            raise Exception("Machine should be stopped")
        self.work_init()
        return self.WorkContinue()

    def Reset(self):
        self.work_init()

    def WorkStop(self):
        self.work_init()
        self.stop = True
        self.finished()
