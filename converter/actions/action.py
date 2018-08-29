import abc
import event

class Action(object):
    def __init__(self, sender, **kwargs):
        self.acted = event.EventEmitter()
        self.sender = sender
        self.completed = False

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

    def __init__(self, feed, acc, **kwargs):
        Action.__init__(self, **kwargs)
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = acc
