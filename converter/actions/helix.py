import euclid3
import time
from enum import Enum
import math

from . import action

class HelixMovement(action.Movement):

    class Axis(Enum):
        xy = 17
        yz = 18
        zx = 19

    def command(self):
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
        delta_cmd = "X%.2fY%.2fZ%.2f" % (self.delta.x, self.delta.y, self.delta.z)
        center_cmd = "I%.2fJ%.2f " % (self.center.x, self.center.y)

        code = type_cmd + feed_cmd + center_cmd + dir_cmd + delta_cmd
        return code

    def __init__(self, delta, r, axis, ccw, feed, acc, **kwargs):
        action.Movement.__init__(self, feed=feed, acc=acc, **kwargs)
        self.axis = axis
        self.ccw = ccw
        self.delta = delta
        self.gcode = None
        self.radius = r

        if axis == self.Axis.xy:
            d = euclid3.Vector2(delta.x, delta.y)
            h = delta.z
        elif axis == self.Axis.yz:
            d = euclid3.Vector2(delta.y, delta.z)
            h = delta.x
        else:
            d = euclid3.Vector2(delta.z, delta.x)
            h = delta.y

        D = d.magnitude()

        if D == 0:
            # line movement along axis
            return

        if r < D / 2:
            raise Exception("Too small radius")
        q = (r**2 - (D/2)**2)**0.5
        # c - center of circle
        # p0 - tangent at begin
        # p1 - tangent at end
        if (ccw is False and r > 0) or (ccw is True and r < 0):
            # Clock wise
            c = euclid3.Vector2(d.x/2 + d.y/D * q, d.y/2 - d.x/D * q)
            if r > 0:
                p0 = euclid3.Vector2(-c.y, c.x)
                p1 = euclid3.Vector2(-(c.y - d.y), c.x - d.x)
            else:
                p0 = euclid3.Vector2(c.y, -c.x)
                p1 = euclid3.Vector2((c.y - d.y), -(c.x - d.x))
        else:
            # Counter clock wise
            c = euclid3.Vector2(d.x/2 - d.y/D * q, d.y/2 + d.x/D * q)
            if r > 0:
                p0 = euclid3.Vector2(c.y, -c.x)
                p1 = euclid3.Vector2(c.y - d.y, -(c.x - d.x))
            else:
                p0 = euclid3.Vector2(-c.y, c.x)
                p1 = euclid3.Vector2(-(c.y - d.y), c.x - d.x)

        self.center = c

        p0 = p0 / p0.magnitude()
        p1 = p1 / p1.magnitude()

        cosa = -c.x * (d.x - c.x) - c.y * (d.y - c.y) / (c.magnitude() * (d - c).magnitude())
        angle = math.acos(cosa)
        if r < 0:
            angle = 2*math.pi - angle
        l = abs(r) * angle
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