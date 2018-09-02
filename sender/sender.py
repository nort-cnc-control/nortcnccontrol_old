#!/usr/bin/env python3

import time
import sys
import serial
import event
import threading
import re

class SerialSender(object):

    class SerialReceiver(threading.Thread):

        def __init__(self, ser, finish_event, ev_completed, ev_started, ev_slots):
            threading.Thread.__init__(self)
            self.ser = ser
            self.finish_event = finish_event
            self.recompleted = re.compile(r"completed N:([0-9]+) Q:([0-9]+).*")
            self.restarted = re.compile(r"started N:([0-9]+) Q:([0-9]+).*")
            self.requeued = re.compile(r"queued N:([0-9]+) Q:([0-9]+).*")
            self.reerror = re.compile(r"error N:([0-9]+).*")
            self.ev_completed = ev_completed
            self.ev_started = ev_started
            self.ev_slots = ev_slots

        def run(self):
            while not self.finish_event.is_set():
                ans = self.ser.readline().decode("utf8")

                match = self.restarted.match(ans)
                if match != None:
                    Nid = match.group(1)
                    self.ev_started(Nid)
                    Q = int(match.group(2))
                    self.ev_slots(Q)
                    continue

                match = self.recompleted.match(ans)
                if match != None:
                    Nid = match.group(1)
                    self.ev_completed(Nid)
                    Q = int(match.group(2))
                    self.ev_slots(Q)
                    continue

                match = self.requeued.match(ans)
                if match != None:
                    Q = int(match.group(2))
                    self.ev_slots(Q)
                    continue
            
                match = self.reerror.match(ans)
                if match != None:
                    Nid = match.group(1)
                    continue

                print("Unknown answer from MCU: %s" % ans)

    completed = event.EventEmitter()
    started = event.EventEmitter()
    __slots = event.EventEmitter()

    def __init__(self, port, bdrate):
        self.id = 0
        self.has_slots = threading.Event()
        self.__qans = threading.Event()
        self.port = port
        self.baudrate = bdrate
        self.ser = serial.Serial(self.port, self.baudrate,
                                 bytesize=8, parity='N', stopbits=1)
        self.finish_event = threading.Event()
        self.listener = self.SerialReceiver(self.ser, self.finish_event,
                                            self.completed, self.started, self.__slots)
        
        self.__slots += self.__on_slots
        self.listener.start()
        self.has_slots.set()

    def __on_slots(self, Q):
        if Q == 0:
            self.has_slots.clear()
        else:
            self.has_slots.set()
        self.__qans.set()

    def send_command(self, command):
        self.__qans.clear()
        cmd = ("N%i" % self.id) + command + "\n"
        self.ser.write(bytes(cmd, "UTF-8"))
        self.ser.flush()
        oid = self.id
        self.id += 1
        self.__qans.wait()
        return oid

    def close(self):
        self.finish_event.set()
        self.ser.close()
