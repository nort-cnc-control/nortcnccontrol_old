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

    def __init__(self, sock):
        self.sock = sock
        self.control = gui.Interface()
        self.control.load_file += self.__load_file
        self.control.reset_clicked += self.__reset
        self.control.start_clicked += self.__start
        self.control.continue_clicked += self.__continue
        self.control.stop_clicked += self.__stop
        self.control.home_clicked += self.__home
        self.control.probe_clicked += self.__probe
        self.control.command_entered += self.__command

        self.control.xp_clicked += self.__xp
        self.control.xm_clicked += self.__xm
        self.control.yp_clicked += self.__yp
        self.control.ym_clicked += self.__ym
        self.control.zp_clicked += self.__zp
        self.control.zm_clicked += self.__zm

        self.sock.settimeout(0)
        self.control.switch_to_initial_mode()

    def __send_command(self, command):
        msg = {
            "type" : "command",
            "command" : command,
        }
        self.msg_sender.send_message(msg)

    def __continue(self):
        self.__send_command("continue")

    def __start(self):
        self.__send_command("start")

    def __reset(self):
        self.__send_command("reset")

    def __stop(self):
        self.__send_command("stop")

    def __command(self, cmd):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : [cmd],
        }
        self.msg_sender.send_message(r)

    def __home(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["G74"],
        }
        self.msg_sender.send_message(r)

    def __probe(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["G30"],
        }
        self.msg_sender.send_message(r)

    def __xp(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["M120", "G91", "G0 X1", "M121"],
        }
        self.msg_sender.send_message(r)

    def __xm(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["M120", "G91", "G0 X-1", "M121"],
        }
        self.msg_sender.send_message(r)

    def __yp(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["M120", "G91", "G0 Y1", "M121"],
        }
        self.msg_sender.send_message(r)

    def __ym(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["M120", "G91", "G0 Y-1", "M121"],
        }
        self.msg_sender.send_message(r)

    def __zp(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["M120", "G91", "G0 Z1", "M121"],
        }
        self.msg_sender.send_message(r)

    def __zm(self):
        r = {
            "type" : "command",
            "command" : "execute",
            "lines" : ["M120", "G91", "G0 Z-1", "M121"],
        }
        self.msg_sender.send_message(r)

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
        elif type == "coordinates":
            hw = msg["hardware"]
            glob = msg["global"]
            loc = msg["local"]
            cs = msg["cs"]
            self.control.set_coordinates(hw, glob, loc, cs)
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
                if msg["display"]:
                    if msg["message"] == "":
                        self.control.show_ok("Finished")
                    else:
                        self.control.show_ok(msg["message"])

    def __on_receive_event(self, sock, cond):
        
        while True:
            try:
                msg, dis = self.msg_receiver.receive_message(wait=False)
                if dis:
                    print("Disconnect")
                    return False
                if msg is None:
                    return True
            except:
                return True
            print(msg)
            self.__process_event(msg)
        return True

    def run(self):
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
    
    remote = ("127.0.0.1", 10000)

    for o, a in optlist:
        if o == "-i":
            infile = a
        elif o == "-h":
            usage()
            sys.exit(0)
        elif o == "-r":
            remote = (a, 10000)

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.connect(remote)

    ctl = Controller(sock)
    ctl.run()
    sys.exit(0)
