import euclid3
import time
from enum import Enum
import math

import common
from common import config

from . import action

class HelixMovement(action.Movement):

    class Axis(Enum):
        xy = 17
        yz = 18
        zx = 19

    def command(self):
        x, y, z = self._convert_axes(self.delta)
        if self.ccw:
            type_cmd = "G3 "
        else:
            type_cmd = "G2 "

        if self.axis == self.Axis.xy:
            dir_cmd = "G17 "
        elif self.axis == self.Axis.yz:
            dir_cmd = "G18 "
        else:
            dir_cmd = "G19 "

        feed_cmd = "F%iP%iL%iT%i " % (self.feed, self.feed0+0.5, self.feed1+0.5, self.acceleration)
        delta_cmd = "X%.2fY%.2fZ%.2f " % (x, y, z)
        center_cmd = "D%.2f " % (self.hcl)

        code = type_cmd + feed_cmd + center_cmd + dir_cmd + delta_cmd
        return code

    def __ps_from_cdr(self, c, d, r, sign):
        if r > 0:
            p0 = euclid3.Vector2(-c.y, c.x)
            p1 = euclid3.Vector2(-(c.y - d.y), c.x - d.x)
        else:
            p0 = euclid3.Vector2(c.y, -c.x)
            p1 = euclid3.Vector2((c.y - d.y), -(c.x - d.x))
        p0 = p0 / p0.magnitude()
        p1 = p1 / p1.magnitude()
        return p0 * sign, p1 * sign

    # length=1 vector, ortogonal to d, and looking right to d
    def __right_ortogonal(self, d):
        D = d.magnitude()
        right = euclid3.Vector2(d.y/D, -d.x/D)
        if self.plane_is_left:
            right = -right
        return right

    # Find center of arc, and tangents on begin and end
    def __find_geometry_from_r(self, d, r, ccw):
        D = d.magnitude()

        if D == 0:
            raise Exception("Line movement")

        if abs(r) < D / 2:
            raise Exception("Too small radius")

        # distance from arc center to horde
        s = (r**2 - (D/2)**2)**0.5

        if (ccw is False and r > 0) or (ccw is True and r < 0):
            # Clock wise or ccw with angle > 180
            # Center is right to horde
            center_side = 1
        else:
            # Counter clock wise or cw with angle > 180
            # Center is left to horde
            center_side = -1

        horde_center_distance = s * center_side
        right = self.__right_ortogonal(d)
        center = euclid3.Vector2(d.x/2 + right.x * horde_center_distance,
                                 d.y/2 + right.y * horde_center_distance)
        #print(center)
        p0, p1 = self.__ps_from_cdr(center, d, r, center_side)

        cosa = 1 - d.magnitude_squared() / (2 * r**2)
        arc_angle = math.acos(cosa)
        if r < 0:
            arc_angle = 2*math.pi - arc_angle

        return center, horde_center_distance, arc_angle, p0, p1

    # Find radius of arc, and tangents on begin and end
    def __find_geometry_from_ijk(self, d, center, ccw):
        D = d.magnitude()

        r1 = center.magnitude()
        r2 = (d - center).magnitude()
        if abs(r1 - r2) > 1:
            raise Exception("Incorrect center position")
        r = (r1 + r2)/2
        
        right = self.__right_ortogonal(d)
        #print(right)
        if right.x * center.x + right.y * center.y > 0:
            center_side = 1
        else:
            center_side = -1
        # distance from arc center to horde
        s = (r**2 - (D/2)**2)**0.5
        
        horde_center_distance = s * center_side
        
        cosa = 1 - d.magnitude_squared() / (2 * r**2)
        arc_angle = math.acos(cosa)

        if (ccw is False and center_side == 1) or (ccw is True and center_side == -1):
            # small arc
            pass
        else:
            # big arc
            arc_angle = 2*math.pi - arc_angle
            r = -r
        
        p0, p1 = self.__ps_from_cdr(center, d, r, center_side)
        return r, horde_center_distance, arc_angle, p0, p1

        
    def __init__(self, delta, axis, ccw, feed, acc, **kwargs):
        action.Movement.__init__(self, feed=feed, acc=acc, **kwargs)
        self.axis = axis
        self.delta = delta
        self.gcode = None
        d, h = self.__get_d_h(delta, axis)

        # Now we don't support 'h'!
        if h != 0:
            raise Exception("Arc don't support 'h'!")

        if axis == self.Axis.xy:
            self.plane_is_left = not common.config.XY_RIGHT
        elif axis == self.Axis.yz:
            self.plane_is_left = not common.config.YZ_RIGHT
        else:
            self.plane_is_left = not common.config.ZX_RIGHT
        
        #if not self.plane_is_left:
        #    self.ccw = ccw
        #else:
        #    self.ccw = not ccw
        self.ccw = ccw
        if "r" in kwargs.keys():
            self.r = kwargs["r"]
            # center - center of circle
            # angle  - angle of arc
            # p0     - tangent at begin
            # p1     - tangent at end
            self.center, self.hcl, angle, p0, p1 = self.__find_geometry_from_r(d, self.r, self.ccw)
        else:
            ci = kwargs["i"]
            cj = kwargs["j"]
            ck = kwargs["k"]
            if axis == self.Axis.xy:
                self.center = euclid3.Vector2(ci, cj)
            elif axis == self.Axis.yz:
                self.center = euclid3.Vector2(cj, ck)
            else:
                self.center = euclid3.Vector2(ck, ci)
            # r     - radius of circle
            # angle - angle of arc
            # p0    - tangent at begin
            # p1    - tangent at end
            self.r, self.hcl, angle, p0, p1 = self.__find_geometry_from_ijk(d, self.center, self.ccw)

        l = abs(self.r) * angle
        self.__set_tan(axis, p0, p1, h, l)

    def __get_d_h(self, delta, axis):
        if axis == self.Axis.xy:
            d = euclid3.Vector2(delta.x, delta.y)
            h = delta.z
        elif axis == self.Axis.yz:
            d = euclid3.Vector2(delta.y, delta.z)
            h = delta.x
        else:
            d = euclid3.Vector2(delta.z, delta.x)
            h = delta.y
        return d, h


    def __set_tan(self, axis, p0, p1, h, l):
        tan = h / l
        tan0 = euclid3.Vector3(p0.x, p0.y, tan)
        tan1 = euclid3.Vector3(p1.x, p1.y, tan)
        tan0 = tan0 / tan0.magnitude()
        tan1 = tan1 / tan1.magnitude()
        if axis == self.Axis.xy:
            self.dir_0 = tan0
            self.dir_1 = tan1
        elif axis == self.Axis.yz:
            self.dir_0 = euclid3.Vector3(tan0.z, tan0.x, tan0.y)
            self.dir_1 = euclid3.Vector3(tan1.z, tan1.x, tan1.y)
        elif axis == self.Axis.zx:
            self.dir_0 = euclid3.Vector3(tan0.y, tan0.z, tan0.x)
            self.dir_1 = euclid3.Vector3(tan1.y, tan1.z, tan1.x)

    def dir0(self):
        return self.dir_0

    def dir1(self):
        return self.dir_1
