import threading
from common import event

class EmulatorSender(object):
    
    queued = event.EventEmitter()
    completed = event.EventEmitter()
    started = event.EventEmitter()
    dropped = event.EventEmitter()
    
    has_slots = threading.Event()

    def __init__(self):
        self.id = 0
        self.has_slots.set()
    
    def send_command(self, command):
        cmd = ("N%i " % self.id) + command + "\n"
        print("Command %s" % cmd)
        self.queued(self.id)
        oid = self.id
        self.started(self.id)
        self.completed(self.id)
        self.id += 1
        return oid
