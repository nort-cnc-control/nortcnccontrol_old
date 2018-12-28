#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc
import os
import socket
import json

import common
import common.jsonwait

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib

from ui import gui

def usage():
    pass



class Controller(object):

    sockpath = "/tmp/cnccontrol"

    def __init__(self):

        self.control = gui.Interface()
        self.control.load_file += self.__load_file
        self.control.start_clicked += self.__start
        self.control.continue_clicked += self.__continue
        self.control.stop_clicked += self.__stop
        self.control.home_clicked += self.__home
        self.control.probe_clicked += self.__probe
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.sock.settimeout(0)
        self.control.switch_to_initial_mode()

    def __send_command(self, command):
        msg = {
            "type" : "command",
            "command" : command,
        }
        ser = json.dumps(msg)
        try:
            self.sock.send(bytes(ser, "utf-8"))
        except Exception as e:
            print(e)

    

    def __continue(self):
        self.__send_command("continue")

    def __home(self):
        self.__send_command("home")

    def __probe(self):
        self.__send_command("probe")

    def __start(self):
        self.__send_command("start")

    def __reset(self):
        self.__send_command("reset")

    def __stop(self):
        self.__send_command("stop")

    def __load_file(self, filename):
        file = open(filename, encoding="utf-8")
        lines = file.readlines()
        file.close()

        cmds = []
        for line in lines:
            cmds.append(line.strip())
        r = {
            "type" : "command",
            "command" : "load",
            "lines" : cmds,
        }
        self.msg_sender.send_message(r)

    def __process_event(self, msg):
        type = msg["type"]
        if type == "loadlines":
            lines = msg["lines"]
            self.control.clear_commands()
            for line in lines:
                self.control.add_command(line)
        elif type == "line":
            line = msg["line"]
            self.control.select_line(line)
        elif type == "state":
            state = msg["state"]
            message = msg["message"]
            if state == "init":
                self.control.switch_to_initial_mode()
            elif state == "running":
                self.control.switch_to_running_mode()
            elif state == "paused":
                self.control.switch_to_paused_mode()
                if message != "":
                    self.control.show_ok(message)
            elif state == "completed":
                self.control.switch_to_initial_mode()
                self.control.show_ok("Finished")

    def __on_receive_event(self, sock, cond):
        
        while True:
            try:
                msg = self.msg_receiver.receive_message(wait=False)
                if msg is None:
                    return True
            except:
                return True
            print(msg)
            self.__process_event(msg)
        return True

    def run(self):
        tmppath = self.sockpath + ".tmp"
        if os.path.exists(tmppath):
            os.remove(tmppath)
        
        self.sock.bind(tmppath)
        self.sock.connect(self.sockpath)

        self.msg_receiver = common.jsonwait.JsonReceiver(self.sock)
        self.msg_sender = common.jsonwait.JsonSender(self.sock)

        GLib.io_add_watch(self.sock, GLib.IO_IN, self.__on_receive_event)
        self.__reset()
        self.control.run()

if __name__ == "__main__":

    infile = None

    try:
        optlist, _ = getopt.getopt(sys.argv[1:], "i:p:b:h")
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)
    
    for o, a in optlist:
        if o == "-i":
            infile = a
        elif o == "-h":
            usage()
            sys.exit(0)

    ctl = Controller()
    ctl.run()
    sys.exit(0)
