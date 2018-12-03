import abc
import event
import threading

# Basic class for all actions
class Action(object):
    def __init__(self, **kwargs):
        self.completed = threading.Event()
        self.action_completed = event.EventEmitter()
        self.action_started = event.EventEmitter()
        self.caching = False

    def run(self):
        return self.act()

    def dispose(self):
        pass

    @abc.abstractmethod
    def act(self):
        return False

    def is_moving(self):
        return False

# Local actions
class InstantAction(Action):

    @abc.abstractmethod
    def perform(self):
        return False

    def act(self):
        self.action_started(self)
        res = self.perform()
        self.completed.set()
        self.action_completed(self)
        return res

# Actions, which generates commands for MCU
class MCUAction(Action):

    def __init__(self, sender, **kwargs):
        Action.__init__(self, **kwargs)
        self.caching = True
        self.sender = sender
        self.Nid = None
        self.sender.completed += self.__received_completed
        self.sender.started += self.__received_started

    @abc.abstractmethod
    def command(self):
        return ""

    def dispose(self):
        self.sender.completed -= self.__received_completed

    def __received_started(self, nid):
        if int(nid) == self.Nid:
            self.action_started(self)

    def __received_completed(self, nid):
        if int(nid) == self.Nid:
            self.completed.set()
            self.action_completed(self)

    def act(self):
        cmd = self.command()
        self.completed.clear()
        self.Nid = self.sender.send_command(cmd)
        return True

# Movement actions
class Movement(MCUAction):
    def is_moving(self):
        return True

    @abc.abstractmethod
    def dir0(self):
        return None

    @abc.abstractmethod
    def dir1(self):
        return None

    def __init__(self, feed, acc, exact_stop, **kwargs):
        MCUAction.__init__(self, **kwargs)
        self.exact_stop = exact_stop
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = acc
