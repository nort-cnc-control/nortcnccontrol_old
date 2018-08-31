#!/usr/bin/env python3

import time
import sys
import serial
import event
import threading
import re

class SerialSender(object):

    class SerialReceiver(threading.Thread):

        def __init__(self, ser, finish_event, ev):
            self.ser = ser
            self.finish_event = finish_event
            self.re = re.compile(r"N:([0-9]+).*")
            self.ev = ev

        def run(self):
            while not self.finish_event.is_set():
                try:
                    ans = self.ser.readline(timeout=1)
                    Nid = self.re.match(ans).group(1)
                    self.ev(Nid)
                except:
                    pass

    completed = event.EventEmitter()

    def __init__(self, port, bdrate):
        self.id = 0
        self.port = port
        self.baudrate = bdrate
        self.ser = serial.Serial(self.port, self.baudrate,
                                 bytesize=8, parity='N', stopbits=1)
        self.finish_event = threading.Event()
        self.listener = self.SerialReceiver(self.ser, self.finish_event, self.completed)

    def send_command(self, command):
        cmd = ("N%i" % self.id) + command + "\n"
        self.ser.write(bytes(cmd, "UTF-8"))
        self.ser.flush()
        oid = self.id
        self.id += 1
        return oid

    def close(self):
        self.ser.close()
