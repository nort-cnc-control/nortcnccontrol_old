import euclid3
from enum import Enum
import common
import copy

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
        offset_1 = 54
        offset_2 = 55
        offset_3 = 56
        offset_4 = 57
        offset_5 = 58
        offset_6 = 59

        def __str__(self):
            if self == self.no_offset:
                return "G53"
            elif self == self.offset_1:
                return "G54"
            elif self == self.offset_2:
                return "G55"
            elif self == self.offset_3:
                return "G56"
            elif self == self.offset_4:
                return "G57"
            elif self == self.offset_5:
                return "G58"
            elif self == self.offset_6:
                return "G59"

    def __init__(self):
        self.feed = common.config.DEFAULT_FEED
        self.fastfeed = common.config.FASTFEED
        self.acc = common.config.ACCELERATION
        self.jerk = common.config.JERKING

        # global coordinates
        self.pos = euclid3.Vector3(0, 0, 0)

        self.motion = self.MotionGroup.fast_move
        self.plane = self.PlaneGroup.xy

        self.r_offset = self.CutterRadiusCompenstationGroup.no_compensation
        self.r_offset_axis = euclid3.Vector3(0, 0, 1)
        self.r_offset_radius = euclid3.Matrix4.new(0,0,0,0,
                                                   0,0,0,0,
                                                   0,0,0,0,
                                                   0,0,0,1)

        self.tool = None
        self.tool_diameter = {}

        self.positioning = self.PositioningGroup.absolute
        self.feed_mode = self.FeedRateGroup.feed
        self.units = self.UnitsGroup.mms
        self.CRC = self.CutterRadiusCompenstationGroup.no_compensation
        self.TLO = self.ToolLengthOffsetGroup.no_compensation
        self.Spindle = self.SpindleSpeedGroup.rpm_speed
        self.canned = self.CannedCyclesGroup.retract_origin
        self.coord_system = self.CoordinateSystemGroup.no_offset

        self.offsets = {
                self.CoordinateSystemGroup.no_offset: self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_1: self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_2: self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_3: self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_4: self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_5: self.CoordinateSystem(0, 0, 0),
                self.CoordinateSystemGroup.offset_6: self.CoordinateSystem(0, 0, 0),
        }

    def __build_offset_matrix(self, r, sign):
        if sign == -1:
            r = -r
        a1 = self.r_offset_axis[0] * r
        a2 = self.r_offset_axis[1] * r
        a3 = self.r_offset_axis[2] * r
        m = euclid3.Matrix4.new(0, a3, -a2, 0,
                                -a3, 0, a1, 0,
                                a2, -a1, 0, 0,
                                0, 0, 0, 1)
        return m

    def process_frame(self, frame):
        for cmd in frame.commands:
            if cmd.type != "G":
                continue
            if cmd.value == 0:
                self.motion = self.MotionGroup.fast_move
            elif cmd.value == 1:
                self.motion = self.MotionGroup.line
            elif cmd.value == 2:
                self.motion = self.MotionGroup.round_cw
            elif cmd.value == 3:
                self.motion = self.MotionGroup.round_ccw
            elif cmd.value == 17:
                self.plane = self.PlaneGroup.xy
            elif cmd.value == 18:
                self.plane = self.PlaneGroup.zx
            elif cmd.value == 19:
                self.plane = self.PlaneGroup.yz
            elif cmd.value == 20:
                self.units = self.UnitsGroup.inches
            elif cmd.value == 21:
                self.units = self.UnitsGroup.mms
            elif cmd.value == 40:
                self.r_offset = self.CutterRadiusCompenstationGroup.no_compensation
                self.r_offset_radius = euclid3.Matrix4.new(0,0,0,0,
                                                           0,0,0,0,
                                                           0,0,0,0,
                                                           0,0,0,1)
            elif cmd.value == 41:
                self.r_offset = self.CutterRadiusCompenstationGroup.compensate_left
                if self.tool in self.tool_diameter:
                    self.r_offset_radius = self.__build_offset_matrix(self.tool_diameter[self.tool]/2, -1)
            elif cmd.value == 42:
                self.r_offset = self.CutterRadiusCompenstationGroup.compensate_right
                if self.tool in self.tool_diameter:
                    self.r_offset_radius = self.__build_offset_matrix(self.tool_diameter[self.tool]/2, 1)
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

    def set_coordinate_system(self, x, y, z):
        if self.coord_system == self.CoordinateSystemGroup.no_offset:
            raise Exception("Can not set offset for global CS")

        offset = self.offsets[self.coord_system]
        if x != None:
            x0 = self.pos.x - x
        else:
            x0 = offset.x

        if y != None:
            y0 = self.pos.y - y
        else:
            y0 = offset.y

        if z != None:
            z0 = self.pos.z - z
        else:
            z0 = offset.z

        cs = self.CoordinateSystem(x0, y0, z0)
        self.offsets[self.coord_system] = cs

    def select_tool(self, tool):
        self.tool = tool
        if self.tool in self.tool_diameter:
            if self.r_offset == self.CutterRadiusCompenstationGroup.no_compensation:
                self.r_offset_radius = euclid3.Matrix4.new(0,0,0,0,
                                                           0,0,0,0,
                                                           0,0,0,0,
                                                           0,0,0,1)
            elif self.r_offset == self.CutterRadiusCompenstationGroup.compensate_left:
                self.r_offset_radius = self.__build_offset_matrix(self.tool_diameter[self.tool]/2, -1)
            elif self.r_offset == self.CutterRadiusCompenstationGroup.compensate_right:
                self.r_offset_radius = self.__build_offset_matrix(self.tool_diameter[self.tool]/2, 1)
        else:
            self.r_offset_radius = 0

    def copy(self):
        return copy.copy(self)
