#!/usr/bin/env python3

import common
import common.jsonwait
import common.config

import sender
import sender.emulatorsender
import sender.serialsender
import sender.spindelemulator
import sender.n700e

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
        try:
            print("Emiting message %s" % str(msg))
            self.msg_sender.send_message(msg)
        except Exception as e:
            print(e)

    def __init__(self, table_sender, spindel_sender, path):
        self.path = path
        if os.path.exists(path):
            os.remove(path)
        self.state = "init"
        self.socket = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.socket.bind(path)
        self.socket.listen(1)

        self.msg_sender = None
        self.msg_receiver = None

        self.running = False
        self.clientaddr = None

        self.table_sender = table_sender
        self.spindel_sender = spindel_sender
        self.machine = machine.machine.Machine(self.table_sender, self.spindel_sender)
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
            self.connection,_ = self.socket.accept()
            self.msg_receiver = common.jsonwait.JsonReceiver(self.connection)
            self.msg_sender = common.jsonwait.JsonSender(self.connection)
            while self.running:
                print("Waiting command")
                msg = self.msg_receiver.receive_message()
                if msg is None:
                    self.connection.close()
                    break

                print("Received: %s" % str(msg))
                
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
                        self.state = "init"
                        self.__print_state()
                    elif msg["command"] == "probe":
                        self.state = "running"
                        self.__print_state()
                        self.machine.MakeProbeZ()
                        self.state = "init"
                        self.__print_state()
                    else:
                        pass

port = "/dev/ttyUSB0"
brate = common.config.BAUDRATE
port_485 = "/dev/ttyUSB1"
n700e_id = 1
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
    elif o in ("-r", "--rs485"):
        port_485 = a
    elif o in ("-b", "--baudrate"):
        brate = int(a)
    else:
        assert False, "unhandled option"


if emulate:
    print("Emulate")
    table_sender = sender.emulatorsender.EmulatorSender()
    spindel_sender = sender.spindelemulator.Spindel_EMU()
else:
    table_sender = sender.serialsender.SerialSender(port, brate)
    spindel_sender = sender.n700e.Spindel_N700E(port_485, n700e_id)

controller = Controller(table_sender, spindel_sender, "/tmp/cnccontrol")
controller.run()
