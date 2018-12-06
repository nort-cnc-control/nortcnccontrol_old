#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc
import threading
import queue

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import GLib

from ui import guithread
from ui.guithread import InterfaceThread

from converter import machine
from converter.machine import Machine
from converter.parser import GLineParser
from converter.machinethread import MachineThread

from sender import serialsender
from sender import emulatorsender

def usage():
    pass


def main():
    
    infile = None
    port = None
    brate = 57600
    
    try:
        optlist, _ = getopt.getopt(sys.argv[1:], "i:p:b:h")
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    for o, a in optlist:
        if o == "-i":
            infile = a
        if o == "-p":
            port = a
        if o == "-b":
            brate = int(a)
        elif o == "-h":
            usage()
            sys.exit(0)

    if port is None:
        print("Please, specify port -p")
        sys.exit(1)

    #sender = serialsender.SerialSender(port, brate)
    sender = emulatorsender.EmulatorSender()

    ctl = Controller(sender, infile)
    ctl.run()
    sys.exit(0)

if __name__ == "__main__":
    main()
