from enum import Enum
import copy

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

    def copy(self):
        return copy.copy(self)
