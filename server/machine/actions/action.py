import abc
import threading

import common
from common import event

# Basic class for all actions
class Action(object):
    def __init__(self, **kwargs):
        self.dropped = False
        self.breaked = False
        self.completed = threading.Event()
        self.finished = threading.Event()
        self.action_completed = event.EventEmitter()
        self.action_started = event.EventEmitter()
        self.caching = False

    def run(self):
        return self.act()

    def dispose(self):
        pass

    def abort(self):
        self.breaked = True
        self.finished.set()

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
        self.finished.set()
        self.action_completed(self)
        return res

# Actions, which generates commands for Tool

class ToolAction(Action):

    def __init__(self, **kwargs):
        Action.__init__(self, **kwargs)
        self.caching = False
        self.sender = None
        self.Nid = -1

    @abc.abstractmethod
    def perform(self):
        return False

    def act(self):
        self.action_started(self)
        res = self.perform()
        self.completed.set()
        self.finished.set()
        self.action_completed(self)
        return res

# Actions, which generates commands for MCU
class MCUAction(Action):

    def __init__(self, sender, **kwargs):
        Action.__init__(self, **kwargs)
        self.caching = True
        self.table_sender = sender
        self.Nid = None
        self.table_sender.dropped += self.__received_dropped
        self.table_sender.completed += self.__received_completed
        self.table_sender.started += self.__received_started
        self.__sending = False

    @abc.abstractmethod
    def command(self):
        return ""

    def dispose(self):
        self.table_sender.dropped -= self.__received_dropped
        self.table_sender.completed -= self.__received_completed
        self.table_sender.started -= self.__received_started
        self.table_sender.queued -= self.__received_queued
        
    def __received_queued(self, nid):
        self.Nid = int(nid)

    def __received_started(self, nid):
        if int(nid) == self.Nid:
            self.action_started(self)

    def __received_dropped(self, nid):
        nid = int(nid)
        if nid == self.Nid:
            print("Action %i dropped" % nid)
            self.dropped = True
            self.finished.set()

    def __received_completed(self, nid):
        nid = int(nid)
        if nid == self.Nid:
            print("Action %i completed" % nid)
            self.completed.set()
            self.finished.set()
            self.action_completed(self)

    def act(self):
        self.table_sender.queued += self.__received_queued
        cmd = self.command()
        self.completed.clear()
        if not self.table_sender.has_slots.is_set():
            print("Waiting for slots")
            self.table_sender.has_slots.wait()
        self.table_sender.send_command(cmd)
        self.table_sender.queued -= self.__received_queued
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

    def _convert_axes(self, delta):
        # inverting axes
        if common.config.X_INVERT:
            x = -delta.x
        else:
            x = delta.x

        if common.config.Y_INVERT:
            y = -delta.y
        else:
            y = delta.y
        
        if common.config.Z_INVERT:
            z = -delta.z
        else:
            z = delta.z
        
        return x, y, z
