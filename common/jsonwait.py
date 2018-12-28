#!/usr/bin/python3

import json

class JsonReceiver(object):

    def __init__(self, sock):
        self.sock = sock
        self.buf = bytes()

    def __acquire_message(self):
        for i in range(1, len(self.buf) + 1):
            head = self.buf[:i]
            try:
                msg = json.loads(head)
                self.buf = self.buf[i:]
                return msg
            except:
                pass
        return None

    def receive_message(self):
        msg = self.__acquire_message()
        if msg != None:
            return msg
        while True:
            ser = self.sock.recv(1024)
            self.buf += ser
            msg = self.__acquire_message()
            if msg != None:
                return msg
        assert(False)

class JsonSender(object):

    def __init__(self, sock):
        self.sock = sock

    def send_message(self, msg):
        ser = bytes(json.dumps(msg), "utf-8")
        self.sock.send(ser)
