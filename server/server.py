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
import signal
import socket
import json

import threading

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
        self.table_sender.protocol_error += self.__protocol_error

        self.spindel_sender = spindel_sender
        self.machine = machine.machine.Machine(self.table_sender, self.spindel_sender)
        self.parser = machine.parser.GLineParser()
        self.machine.paused += self.__continue_on_pause
        self.machine.finished += self.__done
        self.machine.tool_selected += self.__tool_selected
        self.machine.line_selected += self.__line_selected

        self.work_thread = None

    def __protocol_error(self, fatal, msg):
        if fatal:
            self.state = "error"
            os.kill(os.getpid(), signal.SIGKILL)

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

    def __done(self, display, message=""):
        # send RPC message about event
        self.state = "completed"
        self.__emit_message({
            "type" : "state",
            "state" : self.state,
            "message" : message,
            "display" : display,
        })
        self.state = "init"
        self.__print_state()

    def __load_lines(self, lines):
        frames = []
        for line in lines:
            frame = self.parser.parse(line)
            frames.append(frame)
        self.__emit_message({"type":"loadlines", "lines":lines})
        self.machine.Load(frames)
        
    def __execute_line(self, line):
        try:
            frame = self.parser.parse(line)
            self.machine.Execute(frame)
        except Exception as e:
            self.__done(True, "Process error: " + str(e))

    def __print_state(self, message = ""):
        self.__emit_message({
            "type" : "state",
            "state" : self.state,
            "message" : message
        })

    def __run_cmd(self, cmd, *args, wait=True):
        if not wait and self.work_thread is not None:
            if not self.machine.is_running:
                self.work_thread.join()
            else:
                print("Can not run ", cmd, " - still waiting")
                return
        print("RUN = ", cmd)
        self.work_thread = threading.Thread(target=cmd, args=args)
        self.work_thread.start()
        if wait:
            self.work_thread.join()
            self.work_thread = None

    def run(self):
        self.running = True
        while self.running:
            self.connection,_ = self.socket.accept()
            self.msg_receiver = common.jsonwait.JsonReceiver(self.connection)
            self.msg_sender = common.jsonwait.JsonSender(self.connection)
            while self.running:
                print("Waiting command")
                msg, dis = self.msg_receiver.receive_message()
                if dis:
                    self.connection.close()
                    break

                print("Received: %s" % str(msg))
                
                if not ("type" in msg):
                    continue
                if msg["type"] == "getstate":
                    self.__print_state()
                elif msg["type"] == "command":
                    if msg["command"] == "reset":
                        self.__run_cmd(self.machine.WorkReset)
                        self.state = "init"
                        self.__print_state()
                    elif msg["command"] == "start":
                        self.state = "running"
                        self.__print_state()
                        self.__run_cmd(self.machine.WorkStart, wait=False)
                    elif msg["command"] == "continue":
                        self.state = "running"
                        self.__print_state()
                        self.__run_cmd(self.machine.WorkContinue, wait=False)
                    elif msg["command"] == "execute":
                        self.state = "running"
                        self.__print_state()
                        self.__run_cmd(self.__execute_line, msg["line"], wait=False)
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
                        self.__run_cmd(self.machine.WorkStop)
                        self.state = "init"
                        self.__print_state()
                    elif msg["command"] == "home":
                        self.state = "running"
                        self.__print_state()
                        self.__run_cmd(self.__execute_line, "G74", wait=False)
                    elif msg["command"] == "probe":
                        self.state = "running"
                        self.__print_state()
                        self.__run_cmd(self.__execute_line, "G30", wait=False)
                    else:
                        pass

port = common.config.TABLE_PORT
brate = common.config.BAUDRATE
port_485 = common.config.RS485_PORT
n700e_id = common.config.N700E_ID

emulate_t = common.config.EMULATE_TABLE
emulate_s = common.config.EMULATE_SPINDEL

try:
    opts, args = getopt.getopt(sys.argv[1:], "eEp:b:r:", ["port=", "baudrate=", "rs485="])
except getopt.GetoptError as err:
    # print help information and exit:
    print(err) # will print something like "option -a not recognized"
    sys.exit(2)

for o, a in opts:
    if o == "-e":
        emulate_t = True
    elif o == "-E":
        emulate_s = True
    elif o in ("-p", "--port"):
        port = a
    elif o in ("-r", "--rs485"):
        port_485 = a
    elif o in ("-b", "--baudrate"):
        brate = int(a)
    else:
        assert False, "unhandled option"


if emulate_t:
    table_sender = sender.emulatorsender.EmulatorSender()
else:
    table_sender = sender.serialsender.SerialSender(port, brate)

if emulate_s:
    spindel_sender = sender.spindelemulator.Spindel_EMU()
else:
    spindel_sender = sender.n700e.Spindel_N700E(port_485, n700e_id)

controller = Controller(table_sender, spindel_sender, "/tmp/cnccontrol")
controller.run()

