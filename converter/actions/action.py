import abc
import event

class Action(object):
    def __init__(self, **kwargs):
        self.completed = event.EventEmitter()
        self.caching = False

    def run(self):
        return self.act()

    @abc.abstractmethod
    def act(self):
        return False

    def is_moving(self):
        return False

class InstantAction(Action):

    @abc.abstractmethod
    def perform(self):
        return False

    def act(self):
        res = self.perform()
        self.completed(self)
        return res

class MCUAction(Action):

    def __init__(self, sender, **kwargs):
        Action.__init__(self, **kwargs)
        self.caching = True
        self.sender = sender

    @abc.abstractmethod
    def command(self):
        return ""

    def received_completed(self):
        """ Received completed event from MCU """
        self.completed()

    def act(self):
        cmd = self.command()
        self.sender.send_command(cmd)
        return True

class Movement(MCUAction):
    def is_moving(self):
        return True

    @abc.abstractmethod
    def dir0(self):
        return None

    @abc.abstractmethod
    def dir1(self):
        return None

    def __init__(self, feed, acc, **kwargs):
        MCUAction.__init__(self, **kwargs)
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = acc
