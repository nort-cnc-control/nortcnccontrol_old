#!/usr/bin/env python3

import time
import sys
import serial
import event
import threading
import re

class SerialSender(object):

    class SerialReceiver(threading.Thread):

        def __init__(self, ser, finish_event, ev_completed):
            threading.Thread.__init__(self)
            self.ser = ser
            self.finish_event = finish_event
            self.reok = re.compile(r"ok N:([0-9]+).*")
            self.recompleted = re.compile(r"completed N:([0-9]+) Q:([0-9]+).*")
            self.requeued = re.compile(r"queued N:([0-9]+) Q:([0-9]+).*")
            self.reerror = re.compile(r"error N:([0-9]+).*")
            self.ev_completed = ev_completed

        def run(self):
            while not self.finish_event.is_set():
                try:
                    ans = self.ser.readline(timeout=1)
                    Nid = self.reok.match(ans).group(1)
                    self.ev_completed(Nid)
                    continue
                except:
                    pass

                try:
                    ans = self.ser.readline(timeout=1)
                    Nid = self.recompleted.match(ans).group(1)
                    self.ev_completed(Nid)
                    continue
                except:
                    pass

                try:
                    ans = self.ser.readline(timeout=1)
                    Nid = self.requeued.match(ans).group(1)
                    self.ev_completed(Nid)
                    continue
                except:
                    pass
            
                try:
                    ans = self.ser.readline(timeout=1)
                    Nid = self.reerror.match(ans).group(1)
                    self.ev_completed(Nid)
                    continue
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
        self.listener.ev_completed += self.__ev_completed
        self.listener.start()
    
    def __ev_completed(self, id):
        self.completed(id)

    def send_command(self, command):
        cmd = ("N%i" % self.id) + command + "\n"
        self.ser.write(bytes(cmd, "UTF-8"))
        self.ser.flush()
        oid = self.id
        self.id += 1
        return oid

    def close(self):
        self.finish_event.set()
        self.ser.close()
