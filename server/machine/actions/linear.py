import euclid3
import time
import common

from . import action

class LinearMovement(action.Movement):

    def command(self):
        x, y, z = self._convert_axes(self.delta)
        g1 = "G1 F%iP%iL%iT%i " % (self.feed, self.feed0+0.5, self.feed1+0.5, self.acceleration)
        g2 = "X%.2f Y%.2f Z%.2f" % (x, y, z)
        code = g1 + g2
        return code

    def __init__(self, delta, feed, acc, **kwargs):
        action.Movement.__init__(self, feed=feed, acc=acc, **kwargs)
        self.delta = delta
        self.gcode = None
        if self.delta.magnitude() > 0:
            self.dir = self.delta / self.delta.magnitude()
        else:
            self.dir = euclid3.Vector3()

    def dir0(self):
        return self.dir

    def dir1(self):
        return self.dir
