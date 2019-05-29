import threading
from common import event

class EmulatorSender(object):
    
    indexed = event.EventEmitter()
    queued = event.EventEmitter()
    completed = event.EventEmitter()
    started = event.EventEmitter()
    dropped = event.EventEmitter()
    mcu_reseted = event.EventEmitter()
    error = event.EventEmitter()

    has_slots = threading.Event()

    def __init__(self):
        self.id = 0
        self.has_slots.set()
    
    def send_command(self, command, wait=True):
        self.id += 1
        self.indexed(self.id)
        cmd = ("N%i " % self.id) + command + "\n"
        print("Command %s" % cmd)
        self.queued(self.id)
        oid = self.id
        self.started(self.id)
        self.completed(self.id)
        return oid

    def reset(self):
        self.id = 0
