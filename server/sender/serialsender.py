#!/usr/bin/env python3

import time
import sys
import serial
from common import event
import threading
import re

class SerialSender(object):

    class SerialReceiver(threading.Thread):

        def __init__(self, ser, finish_event,
                    ev_completed, ev_started,
                    ev_slots, ev_dropped, ev_queued,
                    ev_protocolerror, ev_mcu_reseted, ev_error):
            threading.Thread.__init__(self)
            self.ser = ser
            self.finish_event = finish_event
            self.re_completed = re.compile(r"completed N:([0-9]+) Q:([0-9]+).*")
            self.re_started = re.compile(r"started N:([0-9]+) Q:([0-9]+).*")
            self.re_queued = re.compile(r"queued N:([0-9]+) Q:([0-9]+).*")
            self.re_dropped = re.compile(r"dropped N:([0-9]+) Q:([0-9]+).*")
            self.re_error = re.compile(r"error.*")
            self.redebug = re.compile(r"debug.*")
            
            self.ev_completed = ev_completed
            self.ev_started = ev_started
            self.ev_slots = ev_slots
            self.ev_queued = ev_queued
            self.ev_dropped = ev_dropped
            self.ev_protocolerror = ev_protocolerror
            self.ev_mcu_reseted = ev_mcu_reseted
            self.ev_error = ev_error

        def run(self):
            while not self.finish_event.is_set():
                resp = None
                try:
                    resp = self.ser.readline()
                except Exception as e:
                    print("Serial port read error", e)
                    self.ev_protocolerror(True, "Serial port read error")
                    break

                try:
                    ans = resp.decode("ascii")
                except:
                    print("Can not decode answer: ", e)
                    self.ev_protocolerror(False, resp)
                    continue

                ans = str(ans).lstrip(chr(0)).strip()
                print("Received answer: [%s], len = %i" % (ans, len(ans)))
                if ans == "Hello":
                    self.ev_mcu_reseted()
                    continue

                match = self.re_started.match(ans)
                if match != None:
                    print("Start received")
                    Nid = match.group(1)
                    self.ev_started(Nid)
                    Q = int(match.group(2))
                    self.ev_slots(Nid, Q)
                    continue

                match = self.re_completed.match(ans)
                if match != None:
                    print("Completed received")
                    Nid = match.group(1)
                    self.ev_completed(Nid)
                    Q = int(match.group(2))
                    self.ev_slots(Nid, Q)
                    continue

                match = self.re_queued.match(ans)
                if match != None:
                    Nid = match.group(1)
                    Q = int(match.group(2))
                    self.ev_queued(Nid)
                    self.ev_slots(Nid, Q)
                    continue

                match = self.re_dropped.match(ans)
                if match != None:
                    Q = int(match.group(2))
                    Nid = match.group(1)
                    self.ev_dropped(Nid)
                    self.ev_slots(Nid, Q)
                    continue

                match = self.re_error.match(ans)
                if match != None:
                    self.ev_error(ans)
                    continue

                match = self.redebug.match(ans)
                if match != None:
                    continue

                print("Unknown answer from MCU: %s" % ans)
                self.ev_protocolerror(ans)

    indexed = event.EventEmitter()
    queued = event.EventEmitter()
    completed = event.EventEmitter()
    dropped = event.EventEmitter()
    started = event.EventEmitter()
    protocol_error = event.EventEmitter()
    mcu_reseted = event.EventEmitter()
    error = event.EventEmitter()

    __reseted_ev = event.EventEmitter()
    has_slots = threading.Event()
    
    def __init__(self, port, bdrate):
        self.__id = 0
        self.__qans = threading.Event()
        self.__reseted = False
        self.__slots = event.EventEmitter()
        self.__finish_event = threading.Event()

        self.port = port
        self.baudrate = bdrate
        self.__ser = serial.Serial(self.port, self.baudrate,
                                 bytesize=8, parity='N', stopbits=1)
        self.__listener = self.SerialReceiver(self.__ser, self.__finish_event,
                                              self.completed, self.started, self.__slots,
                                              self.dropped, self.queued,
                                              self.protocol_error, self.__reseted_ev, self.error)
        self.__reseted_ev += self.__on_reset
        self.__slots += self.__on_slots
        self.__listener.start()
        self.has_slots.set()

    def __on_reset(self):
        self.has_slots.set()
        self.mcu_reseted()

    def __on_slots(self, Nid, Q):
        Nid = int(Nid)
        if Q == 0:
            self.has_slots.clear()
        else:
            self.has_slots.set()
        if Nid != self.__id:
            return

    def send_command(self, command):
        self.__id += 1
        self.__reseted = False
        self.indexed(self.__id)
        cmd = ("N%i " % self.__id) + command
        encoded = bytes(cmd, "ascii")
        s = sum(encoded)
        crc = bytes("*%X" % s, "ascii")
        msg = encoded + crc + b'\n'
        print("Sending command %s" % msg)
        self.__ser.write(msg)
        self.__ser.flush()
        oid = self.__id
        return oid

    def close(self):
        self.__finish_event.set()
        self.__ser.close()

    def reset(self):
        self.__reseted = True
        self.__qans.set()
