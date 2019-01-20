#!/usr/bin/python3

import json
import re

class JsonReceiver(object):

    def __init__(self, sock):
        self.sock = sock
        self.buf = bytes()
        self.relen = re.compile(r"Length: (\d+)")

    def __acquire_msg(self):
        try:
            print("buf0 = ", self.buf)
            start = self.buf.find(b"\x00")
            if start < 0:
                return None
            self.buf = self.buf[start + 1:]
            print("buf1 = ", self.buf)
            end = self.buf.find(b"\xFF")
            if end < 0:
                return None
            msgbuf = self.buf[:end]
            print("msgbuf = ", msgbuf)
            msg = json.loads(msgbuf)
            self.buf = self.buf[end + 1:]
            return msg
        except:
            return None

    def receive_message(self, wait=True):
        msg = self.__acquire_msg()
        if msg != None:
            return msg
        while True:
            ser = self.sock.recv(1024)
            if ser is None or len(ser) == 0:
                return None
            self.buf += ser
            msg = self.__acquire_msg()
            if msg != None or wait == False:
                return msg
        return None

class JsonSender(object):

    def __init__(self, sock):
        self.sock = sock

    def send_message(self, msg):
        ser = bytes(json.dumps(msg), "utf-8")
        msg = b""
        msg += b"\x00"
        msg += ser
        msg += b"\xFF"
        print("Sending: ", msg)
        self.sock.send(msg)
