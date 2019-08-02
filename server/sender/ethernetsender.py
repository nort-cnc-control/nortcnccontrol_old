#!/usr/bin/env python3

import time
import sys
import socket
from common import event
import threading
import re
from sender import answer
import fcntl
import struct

class EthernetSender(object):

    class EthernetReceiver(threading.Thread):

        def __init__(self, sock, remote, finish_event,
                    ev_completed, ev_started,
                    ev_slots, ev_dropped, ev_queued,
                    ev_protocolerror, ev_mcu_reseted, ev_error):
            threading.Thread.__init__(self)
            self.sock = sock
            self.remote = remote
            self.finish_event = finish_event

            self.ev_completed = ev_completed
            self.ev_started = ev_started
            self.ev_slots = ev_slots
            self.ev_queued = ev_queued
            self.ev_dropped = ev_dropped
            self.ev_protocolerror = ev_protocolerror
            self.ev_mcu_reseted = ev_mcu_reseted
            self.ev_error = ev_error

        def run(self):
            print("START RECEIVER")
            while not self.finish_event.is_set():
                resp = None
                try:
                    resp = self.sock.recv(1500)
                except Exception as e:
                    print("Ethernet read error", e)
                    self.ev_protocolerror(True, "Ethernet read error")
                    break
                #dst = resp[0:6]
                src = resp[6:12]
                ethtype = resp[12]*256 +resp[13] 
                #length = resp[14]*256 + resp[15]
                msg = resp[16:]
                if ethtype != 0xFEFE:
                    continue
                self.remote["mac"] = src
                try:
                    ans = msg.decode("ascii").replace("\x00", "")
                except:
                    print("Can not decode answer: ", e)
                    self.ev_protocolerror(False, resp)
                    continue

                print("Received answer: [%s], len = %i" % (ans, len(ans)))
                
                evt = answer.parse_answer(ans)
                if evt["result"] == "ok":
                    if evt["event"] == "queue":
                        self.ev_slots(evt["action"], evt["slots"])
                        self.ev_queued(evt["action"])
                    elif evt["event"] == "drop":
                        self.ev_slots(evt["action"], evt["slots"])
                        self.ev_dropped(evt["action"])
                    elif evt["event"] == "start":
                        self.ev_slots(evt["action"], evt["slots"])
                        self.ev_started(evt["action"])
                    elif evt["event"] == "complete":
                        self.ev_slots(evt["action"], evt["slots"])
                        self.ev_completed(evt["action"])
                    elif evt["event"] == "init":
                        self.ev_mcu_reseted()
                    elif evt["event"] == "error":
                        self.ev_error(evt["msg"])
                else:
                    print("problem", evt)

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
    
    @staticmethod
    def __getHwAddr(ifname):
        s = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
        info = fcntl.ioctl(s.fileno(), 0x8927,  struct.pack('256s', bytes(ifname, 'utf-8')[:15]))
        return info[18:24]

    def __init__(self, ethname, timeout=0, debug=False):
        self.__id = 0
        self.__ethertype = bytes([0xFE, 0xFE])
        self.__remote = {
            "inited" : False,
            "mac" : bytes([255,255,255,255,255,255])
        }
        self.__localmac = self.__getHwAddr(ethname)
        self.__qans = threading.Event()
        self.__reseted = False
        self.__slots = event.EventEmitter()
        self.__finish_event = threading.Event()

        self.__sock = socket.socket(socket.AF_PACKET, socket.SOCK_RAW)
        self.__sock.bind((ethname, socket.htons(0xFEFE)))
        self.timeout = timeout

        self.__listener = self.EthernetReceiver(self.__sock, self.__remote, self.__finish_event,
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

    def send_command(self, command, wait=True):
        self.__id += 1
        self.__reseted = False
        self.indexed(self.__id)
        cmd = ("N%i " % self.__id) + command
        encoded = bytes(cmd, "ascii")
        s = sum(encoded)
        crc = bytes("*%X" % s, "ascii")
        msg = encoded + crc + b'\n'
        msglen = len(msg)
        lenb = bytes([int(msglen / 256), int(msglen % 256)])
        print("Sending command %s" % msg)
        frame = self.__remote["mac"] + self.__localmac + self.__ethertype + lenb + msg
        self.__sock.send(frame)
        oid = self.__id
        return oid

    def close(self):
        self.__finish_event.set()
        self.__sock.close()

    def clean(self):
        self.__reseted = True
        self.__qans.set()

    def reset(self):
        self.__remote["mac"] = bytes([255,255,255,255,255,255])

