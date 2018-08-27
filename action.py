import abc
import event

class Action(object):
    def __init__(self):
        self.acted = event.EventEmitter()

    def run(self):
        res = self.act()
        self.acted()
        return res

    @abc.abstractmethod
    def act(self):
        return False

    def is_moving(self):
        return False

class Movement(Action):
    def is_moving(self):
        return True

    def act(self):
        return self.emit_code()

    @abc.abstractmethod
    def emit_code(self):
        return False

    @abc.abstractmethod
    def dir0(self):
        return None

    @abc.abstractmethod
    def dir1(self):
        return None

    def __init__(self, feed, acc):
        Action.__init__(self)
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = acc
