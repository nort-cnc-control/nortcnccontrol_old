import euclid3
import time
from enum import Enum
import math

import common
from common import config

from . import action

threshold = 1e-4

class HelixMovement(action.Movement):

    class Axis(Enum):
        xy = 17
        yz = 18
        zx = 19

    def command(self):
        x, y, z = self._convert_axes(self.delta)
        ccw = self.ccw
        left = False
        hcl = self.hcl
        if self.axis == HelixMovement.Axis.xy:
            dir_cmd = "G17 "
            if config.X_INVERT:
                left = not left
            if config.Y_INVERT:
                left = not left
        elif self.axis == HelixMovement.Axis.yz:
            dir_cmd = "G18 "
            if config.Y_INVERT:
                left = not left
            if config.Z_INVERT:
                left = not left
        else:
            dir_cmd = "G19 "
            if config.Z_INVERT:
                left = not left
            if config.X_INVERT:
                left = not left
        if left:
            ccw = not ccw
            hcl = -hcl
        
        if ccw:
            type_cmd = "G3 "
        else:
            type_cmd = "G2 "

        feed_cmd = "F%iP%iL%iT%i " % (self.feed, self.feed0+0.5, self.feed1+0.5, self.acceleration)
        delta_cmd = "X%.2fY%.2fZ%.2f " % (x, y, z)
        center_cmd = "D%.2f " % hcl

        code = type_cmd + feed_cmd + center_cmd + dir_cmd + delta_cmd
        return code

    # find tangents to arc
    @staticmethod
    def __find_tangents(start_to_center, end_to_center, ccw, big):
        p0 = euclid3.Vector2(-start_to_center.y, start_to_center.x)
        p1 = euclid3.Vector2(-end_to_center.y, end_to_center.x)

        p0 = p0 / p0.magnitude()
        p1 = p1 / p1.magnitude()

        if ccw:
            p0 *= -1
            p1 *= -1
        
        return p0, p1

    # length=1 vector, ortogonal to d, and looking right to d
    @staticmethod
    def __right_ortogonal_vector(d):
        D = d.magnitude()
        right = euclid3.Vector2(d.y/D, -d.x/D)
        return right

    @staticmethod
    def __find_center_side(source_to_center, delta):
        right = HelixMovement.__right_ortogonal_vector(delta)
        if right.x * source_to_center.x + right.y * source_to_center.y > 0:
            center_side = 1
        else:
            center_side = -1
        return center_side
        
    # Find center of arc, and tangents on begin and end
    @staticmethod
    def __find_geometry_from_r(delta, radius, ccw):
        D = delta.magnitude()
        big_arc = radius < 0
        radius = abs(radius)
        if D == 0:
            raise Exception("Empty movement")

        if radius < D / 2:
            raise Exception("Too small radius")

        # distance from arc center to horde
        s = (radius**2 - (D/2)**2)**0.5

        if (ccw is False and not big_arc) or (ccw is True and big_arc):
            # Clock wise or ccw with angle > 180
            # Center is right to horde
            center_side = 1
        else:
            # Counter clock wise or cw with angle > 180
            # Center is left to horde
            center_side = -1

        horde_center_distance = s * center_side
        right = HelixMovement.__right_ortogonal_vector(delta)
        start_to_center = euclid3.Vector2(right.x * horde_center_distance + delta.x/2,
                                          right.y * horde_center_distance + delta.y/2)
        end_to_center = euclid3.Vector2(right.x * horde_center_distance - delta.x/2,
                                        right.y * horde_center_distance - delta.y/2)

        p0, p1 = HelixMovement.__find_tangents(start_to_center, end_to_center, ccw, big_arc)

        sina = D/(2 * radius)
        if sina > 1 and sina < 1 + threshold:
            sina = 1
        if sina < -1 and sina > -1 - threshold:
            sina = -1

        arc_angle = 2 * math.asin(sina)
        if big_arc:
            arc_angle = 2*math.pi - arc_angle

        return start_to_center, p0, p1, arc_angle

    # Find radius of arc, and tangents on begin and end
    @staticmethod
    def __find_geometry_from_ijk(delta, start_to_center, ccw):
        D = delta.magnitude()
        end_to_center = start_to_center - delta
        r1 = start_to_center.magnitude()
        r2 = end_to_center.magnitude()
        if abs(r1 - r2) > 2:
            raise Exception("Incorrect center position, %lf != %lf" % (r1, r2))
        radius = (r1 + r2)/2

        center_side = HelixMovement.__find_center_side(start_to_center, delta)
        if (center_side == -1 and ccw) or (center_side == 1 and not ccw):
            big_arc = False
        else:
            big_arc = True

        p0, p1 = HelixMovement.__find_tangents(start_to_center, end_to_center, ccw, big_arc)
        sina = D/(2 * radius)
        if sina > 1 and sina < 1 + threshold:
            sina = 1
        if sina < -1 and sina > -1 - threshold:
            sina = -1
        
        arc_angle = 2 * math.asin(sina)
        if big_arc:
            arc_angle = 2*math.pi - arc_angle
        
        return radius, p0, p1, arc_angle

    @staticmethod
    def __get_d_h(delta, axis):
        if axis == HelixMovement.Axis.xy:
            d = euclid3.Vector2(delta.x, delta.y)
            h = delta.z
        elif axis == HelixMovement.Axis.yz:
            d = euclid3.Vector2(delta.y, delta.z)
            h = delta.x
        else:
            d = euclid3.Vector2(delta.z, delta.x)
            h = delta.y
        return d, h

    @staticmethod
    def find_geometry(source, target, ccw, axis, **kwargs):
        d, h = HelixMovement.__get_d_h(target - source, axis)

        # Now we don't support 'h'!
        if abs(h) > 1e-4:
            raise Exception("Arc don't support 'h'!")

        if "r" in kwargs.keys():
            radius = kwargs["r"]
            start_to_center, tan0, tan1, arc_angle = HelixMovement.__find_geometry_from_r(d, radius, ccw)
        else:
            if axis == HelixMovement.Axis.xy:
                start_to_center = euclid3.Vector2(kwargs["i"], kwargs["j"])
            elif axis == HelixMovement.Axis.yz:
                start_to_center = euclid3.Vector2(kwargs["j"], kwargs["k"])
            else:
                start_to_center = euclid3.Vector2(kwargs["k"], kwargs["i"])
            radius, tan0, tan1, arc_angle = HelixMovement.__find_geometry_from_ijk(d, start_to_center, ccw)

        if axis == HelixMovement.Axis.xy:
            dir_0 = euclid3.Vector3(tan0.x, tan0.y, 0)
            dir_1 = euclid3.Vector3(tan1.x, tan1.y, 0)
            center = source + euclid3.Vector3(start_to_center[0], start_to_center[1], 0)
        elif axis == HelixMovement.Axis.yz:
            dir_0 = euclid3.Vector3(0, tan0.x, tan0.y)
            dir_1 = euclid3.Vector3(0, tan1.x, tan1.y)
            center = source + euclid3.Vector3(0, start_to_center[0], start_to_center[1])
        elif axis == HelixMovement.Axis.zx:
            dir_0 = euclid3.Vector3(tan0.y, 0, tan0.x)
            dir_1 = euclid3.Vector3(tan1.y, 0, tan1.x)
            center = source + euclid3.Vector3(start_to_center[1], 0, start_to_center[0])

        return center, dir_0, dir_1, arc_angle

    @staticmethod
    def __find_horde_center_distance(radius, delta, center_side):
        s = (radius**2 - (delta/2)**2)**0.5
        horde_center_distance = s * center_side
        arc_angle = 2 * math.asin(delta/2 / radius)
        return horde_center_distance, arc_angle

    def __init__(self, delta, source_to_center, axis, ccw, feed, acc, **kwargs):
        action.Movement.__init__(self, feed=feed, acc=acc, **kwargs)
        self.axis = axis
        self.delta = delta
        self.gcode = None
        self.ccw = ccw
        d, h = HelixMovement.__get_d_h(self.delta, axis)

        # Now we don't support 'h'!
        if abs(h) > 1e-4:
            raise Exception("Arc doesn't support 'h'!")

        radius = (source_to_center.magnitude() + (source_to_center - delta).magnitude())/2

        center_side = HelixMovement.__find_center_side(source_to_center, delta)
        if (center_side == -1 and ccw) or (center_side == 1 and not ccw):
            big_arc = False
        else:
            big_arc = True
        
        self.hcl, self.angle = HelixMovement.__find_horde_center_distance(radius, d.magnitude(), center_side)
        if big_arc:
            self.angle = 2*math.pi - self.angle
        
        self._length = self.angle * radius
        if self._length == 0:
            print("Len = 0")
            print("radius = ", radius)
            print("angle = ", self.angle)

    def length(self):
        return self._length
