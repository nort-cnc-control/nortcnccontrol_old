#!/usr/bin/env python3
import pyrdpos
import time
import sys
import serial
from common import event
import threading
import re
from sender import answer

class RDPoSSender(object):
    
    indexed = event.EventEmitter()
    queued = event.EventEmitter()
    completed = event.EventEmitter()
    dropped = event.EventEmitter()
    started = event.EventEmitter()
    protocol_error = event.EventEmitter()
    mcu_reseted = event.EventEmitter()
    error = event.EventEmitter()

    __reseted_ev = event.EventEmitter()
    __slots = event.EventEmitter()

    has_slots = threading.Event()
    
    class ReadingThread(threading.Thread):
        def __init__(self, conn, inited, slots, queued, dropped, started, completed, error):
            threading.Thread.__init__(self)
            self.conn = conn
            self.inited = inited
            self.slots = slots
            self.queued = queued
            self.dropped = dropped
            self.started = started
            self.completed = completed
            self.error = error

        def run(self):
            while True:
                msg = self.conn.read()
                if msg is None:
                    break
                evt = answer.parse_answer(msg)
                if evt["result"] == "ok":
                    if evt["event"] == "queue":
                        self.slots(evt["slots"])
                        self.queued(evt["action"])
                    elif evt["event"] == "drop":
                        self.slots(evt["slots"])
                        self.dropped(evt["action"])
                    elif evt["event"] == "start":
                        self.slots(evt["slots"])
                        self.started(evt["action"])
                    elif evt["event"] == "complete":
                        self.slots(evt["slots"])
                        self.completed(evt["action"])
                    elif evt["event"] == "init":
                        self.inited()
                    elif evt["event"] == "error":
                        self.error(evt["msg"])

    def __init__(self, port, bdrate, debug=False):
        self.__id = 0
        self.__qans = threading.Event()

        self.__finish_event = threading.Event()

        self.port = port
        self.baudrate = bdrate
        self.__ser = serial.Serial(self.port, self.baudrate, bytesize=8, parity='N', stopbits=1)
        self.__conn = pyrdpos.RDPoSConnection(self.__ser, debug)
        self.__conn.connect(1, 1)
        print("Connected")
        self.rthr = self.ReadingThread(self.__conn, self.mcu_reseted, self.__slots, self.queued, self.dropped, self.started, self.completed, self.error)
        self.rthr.start()
        self.has_slots.set()

    def send_command(self, command, wait=True):
        self.__id += 1
        self.indexed(self.__id)
        cmd = "N%i %s" % (self.__id, command)
        print("Sending command %s" % cmd)
        if wait:
            self.__conn.send(bytes(cmd, "ascii"))
        else:
            self.__conn.send_nowait(bytes(cmd, "ascii"))
        return  self.__id

    def close(self):
        self.__conn.close()
        self.__ser.close()

    def clean(self):
        pass

    def reset(self):
        print("Reseting connection")
        self.__conn.reset()
        self.__conn.connect(1,1)
        print("Connected")

