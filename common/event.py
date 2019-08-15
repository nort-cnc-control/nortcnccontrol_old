#!/usr/bin/env python3

class EventEmitter(object):

    def __init__(self):
        self.handlers = []

    def __call__(self, *args, **kwargs):
        for hdl in self.handlers:
            hdl(*args, **kwargs)

    def __iadd__(self, handler):
        self.handlers.append(handler)
        return self

    def __isub__(self, handler):
        if handler in self.handlers:
            self.handlers.remove(handler)
        return self

    def dispose(self):
        self.handlers = []
