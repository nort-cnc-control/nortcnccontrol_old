#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc
import os
import socket
import json

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
        self.sock = socket.socket(socket.AF_UNIX, socket.SOCK_DGRAM)

    def __send_command(self, command):
        r = {
            "type" : "command",
            "command" : command,
        }
        self.sock.send(bytes(json.dumps(r), "utf-8"))

    def __continue(self):
        self.__send_command("continue")

    def __start(self):
        self.__send_command("start")

    def __load_file(self, filename):
        pass

    def __on_receive_event(self, sock, cond):
        res = sock.recv(1024)
        try:
            res = res.decode("utf-8")
            data = json.loads(res)
            print(data)
        except:
            pass
        return True

    def run(self):
        tmppath = self.sockpath + ".tmp"
        if os.path.exists(tmppath):
            os.remove(tmppath)
        
        self.sock.bind(tmppath)
        self.sock.connect(self.sockpath)

        GLib.io_add_watch(self.sock, GLib.IO_IN, self.__on_receive_event)
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