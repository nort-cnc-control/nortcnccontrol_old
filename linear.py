import euclid3
import action

class LinearMovement(action.Movement):

    def emit_code(self):
        g1 = "G1F%iP%iL%iT%i " % (self.feed, self.feed0+0.5, self.feed1+0.5, self.acceleration)
        g2 = "X%.2f Y%.2f Z%.2f" % (self.delta.x, self.delta.y, self.delta.z)
        code = g1 + g2
        print(code)

    def __init__(self, delta, feed, acc):
        action.Movement.__init__(self, feed=feed, acc=acc)
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
