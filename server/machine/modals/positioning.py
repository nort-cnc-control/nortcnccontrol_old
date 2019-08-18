import euclid3
from enum import Enum
import common
import copy

class Configuration(object):

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
        self.motion = self.MotionGroup.fast_move
        self.plane = self.PlaneGroup.xy

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


class PositioningState(object):

    def __init__(self):
        # global coordinates
        self.pos = euclid3.Vector3(0, 0, 0)

        # modals
        self.modals = Configuration()
        self.mstack = []

    def __push(self):
        self.mstack.append(copy.copy(self.modals))

    def __pop(self):
        if len(self.mstack) == 0:
            return
        self.modals = self.mstack[-1]
        self.mstack = self.mstack[:len(self.mstack)-1]

    def __process_G(self, cmd):
        if cmd.value == 0:
            self.modals.motion = Configuration.MotionGroup.fast_move
        elif cmd.value == 1:
            self.modals.motion = Configuration.MotionGroup.line
        elif cmd.value == 2:
            self.modals.motion = Configuration.MotionGroup.round_cw
        elif cmd.value == 3:
            self.modals.motion = Configuration.MotionGroup.round_ccw
        elif cmd.value == 17:
            self.modals.plane = Configuration.PlaneGroup.xy
        elif cmd.value == 18:
            self.modals.plane = Configuration.PlaneGroup.zx
        elif cmd.value == 19:
            self.modals.plane = Configuration.PlaneGroup.yz
        elif cmd.value == 20:
            self.modals.units = Configuration.UnitsGroup.inches
        elif cmd.value == 21:
            self.modals.units = Configuration.UnitsGroup.mms
        elif cmd.value == 53:
            self.modals.coord_system = Configuration.CoordinateSystemGroup.no_offset
        elif cmd.value == 54:
            self.modals.coord_system = Configuration.CoordinateSystemGroup.offset_1
        elif cmd.value == 55:
            self.modals.coord_system = Configuration.CoordinateSystemGroup.offset_2
        elif cmd.value == 56:
            self.modals.coord_system = Configuration.CoordinateSystemGroup.offset_3
        elif cmd.value == 57:
            self.modals.coord_system = Configuration.CoordinateSystemGroup.offset_4
        elif cmd.value == 58:
            self.modals.coord_system = Configuration.CoordinateSystemGroup.offset_5
        elif cmd.value == 59:
            self.modals.coord_system = Configuration.CoordinateSystemGroup.offset_6
        elif cmd.value == 90:
            self.modals.positioning = Configuration.PositioningGroup.absolute
        elif cmd.value == 91:
            self.modals.positioning = Configuration.PositioningGroup.relative
        elif cmd.value == 94:
            self.modals.feed_mode = Configuration.FeedRateGroup.feed

    def __process_M(self, cmd):
        if cmd.value == 120:
            self.__push()
        elif cmd.value == 121:
            self.__pop()

    def process_frame(self, frame):
        for cmd in frame.commands:
            if cmd.type == "G":
                self.__process_G(cmd)
            elif cmd.type == "M":
                self.__process_M(cmd)

    def set_coordinate_system(self, x, y, z):
        if self.modals.coord_system == Configuration.CoordinateSystemGroup.no_offset:
            raise Exception("Can not set offset for global CS")

        offset = self.modals.offsets[self.modals.coord_system]
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

        cs = Configuration.CoordinateSystem(x0, y0, z0)
        self.modals.offsets[self.modals.coord_system] = cs

    def copy(self):
        return copy.copy(self)
