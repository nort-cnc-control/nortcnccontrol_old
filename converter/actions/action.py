import abc
import event
import threading

class Action(object):
    def __init__(self, **kwargs):
        self.completed = threading.Event()
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

class InstantAction(Action):

    @abc.abstractmethod
    def perform(self):
        return False

    def act(self):
        res = self.perform()
        self.completed.set()
        return res

class MCUAction(Action):

    def __init__(self, sender, **kwargs):
        Action.__init__(self, **kwargs)
        self.caching = True
        self.sender = sender
        self.Nid = None
        self.sender.completed += self.__received_completed

    @abc.abstractmethod
    def command(self):
        return ""

    def dispose(self):
        self.sender.completed -= self.__received_completed

    def __received_completed(self, nid):
        if nid == self.Nid:
            self.completed.set()
            self.sender.completed -= self.__received_completed

    def act(self):
        cmd = self.command()
        self.completed.clear()
        self.Nid = self.sender.send_command(cmd)
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
