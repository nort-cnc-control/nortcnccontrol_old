#!/usr/bin/env python3

import sender
import sender.emulatorsender
import sender.serialsender

import machine
import machine.machine
import machine.parser

import getopt
import sys

import os
import socket
import json

class Controller(object):
    def __emit_message(self, msg):
        if self.clientaddr is None:
            print("No client addr")
            return
        msg["source"] = "server"
        ser = json.dumps(msg)
        #print("sending: ", ser)
        self.socket.sendto(bytes(ser, "utf-8"), self.clientaddr)

    def __wait_message(self):
        while True:
            ser, addr = self.socket.recvfrom(1024)
            
            if ser is None or len(ser) == 0:
                continue
            try:
                msg = json.loads(ser)
                if "source" in msg and msg["source"] == "server":
                    continue
                return msg, addr
            except:
                continue
        assert(False)

    def __init__(self, sender, path):
        self.path = path
        if os.path.exists(path):
            os.remove(path)
        self.state = "init"
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)
        self.socket.bind(path)

        self.running = False
        self.clientaddr = None

        self.sender = sender
        self.machine = machine.machine.Machine(self.sender)
        self.parser = machine.parser.GLineParser()
        self.machine.paused += self.__continue_on_pause
        self.machine.finished += self.__done

    def __continue_on_pause(self, reason):
        # send RPC message about event
        self.state = "paused"
        self.print_state(reason)

    def __done(self):
        # send RPC message about event
        self.state = "completed"
        self.print_state()
        self.state = "init"
        self.print_state()

    def load(self, lines):
        frames = []
        for line in lines:
            frame = self.parser.parse(line)
            frames.append(frame)
        self.machine.load(frames)

    def print_state(self, message = ""):
        self.__emit_message({
            "type" : "state",
            "state" : self.state,
            "message" : message
        })

    def run(self):    
        self.running = True
        while self.running:
            msg, addr = self.__wait_message()
            self.clientaddr = addr

            #print("Received: %s" % str(msg))
            if not ("type" in msg):
                continue
            if msg["type"] == "getstate":
                self.print_state()
            elif msg["type"] == "command":
                if msg["command"] == "start":
                    self.state = "running"
                    self.print_state()
                    self.machine.work_start()
                elif msg["command"] == "continue":
                    self.state = "running"
                    self.print_state()
                    self.machine.work_continue()
                elif msg["command"] == "exit":
                    self.state = "exit"
                    self.print_state()
                    self.running = False
                elif msg["command"] == "load":
                    lines = msg["lines"]
                    self.load(lines)
                    self.state = "init"
                else:
                    pass

sender = sender.emulatorsender.EmulatorSender()
controller = Controller(sender, "/tmp/cnccontrol")
controller.run()
