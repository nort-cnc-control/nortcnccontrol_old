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
        try:
            self.socket.sendto(bytes(ser, "utf-8"), self.clientaddr)
        except Exception as e:
            print(e)

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
        self.machine.tool_selected += self.__tool_selected
        self.machine.line_selected += self.__line_selected

    def __continue_on_pause(self, reason):
        # send RPC message about event
        self.state = "paused"
        self.__print_state("Pause")

    def __line_selected(self, line):
        self.__emit_message({"type": "line", "line": line})

    def __tool_selected(self, tool):
        # send RPC message about event
        self.state = "paused"
        self.__print_state("Please insert tool #%i" % tool)

    def __done(self):
        # send RPC message about event
        self.state = "completed"
        self.__print_state()
        self.state = "init"
        self.__print_state()

    def __load_lines(self, lines):
        frames = []
        for line in lines:
            frame = self.parser.parse(line)
            frames.append(frame)
        self.machine.Load(frames)
        self.__emit_message({"type":"loadlines", "lines":lines})

    def __print_state(self, message = ""):
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
                self.__print_state()
            elif msg["type"] == "command":
                if msg["command"] == "reset":
                    self.state = "init"
                    self.machine.Reset()
                    self.__print_state()
                elif msg["command"] == "start":
                    self.state = "running"
                    self.__print_state()
                    self.machine.WorkStart()
                elif msg["command"] == "continue":
                    self.state = "running"
                    self.__print_state()
                    self.machine.WorkContinue()
                elif msg["command"] == "exit":
                    self.state = "exit"
                    self.__print_state()
                    self.running = False
                elif msg["command"] == "load":
                    lines = msg["lines"]
                    self.__load_lines(lines)
                    self.state = "init"
                    self.__print_state("G-Code loaded")
                elif msg["command"] == "stop":
                    self.machine.WorkStop()
                    self.state = "init"
                    self.__print_state()
                elif msg["command"] == "home":
                    self.state = "running"
                    self.__print_state()
                    self.machine.MakeHoming(True, True, True)
                    self.state = "stopped"
                else:
                    pass

port = "/dev/ttyUSB0"
brate = 57600
emulate = False

try:
    opts, args = getopt.getopt(sys.argv[1:], "ep:b:", ["emulate", "port=", "baudrate="])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    sys.exit(2)

for o, a in opts:
    if o == "-e":
        emulate = True
    elif o in ("-p", "--port"):
        port = a
    elif o in ("-b", "--baudrate"):
        brate = int(a)
    else:
        assert False, "unhandled option"


if emulate:
    print("Emulate")
    sender = sender.emulatorsender.EmulatorSender()
else:
    sender = sender.serialsender.SerialSender(port, brate)

controller = Controller(sender, "/tmp/cnccontrol")
controller.run()
