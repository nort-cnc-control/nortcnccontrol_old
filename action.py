import abc

class Action(object):
    @abc.abstractmethod
    def act(self):
        pass

    def is_moving(self):
        return False

class Movement(Action):
    def is_moving(self):
        return True

    def act(self):
        self.emit_code()

    @abc.abstractmethod
    def emit_code(self):
        pass

    @abc.abstractmethod
    def dir0(self):
        return None

    @abc.abstractmethod
    def dir1(self):
        return None

    def __init__(self, feed, acc):
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = acc
