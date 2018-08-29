#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc
import threading

from gui import Interface
from machine import Machine
from parser import GLineParser
from machinethread import MachineThread

def usage():
    pass

class Controller(object):

    def __init__(self, file = None):
        self.frames = []
        self.interface = Interface()
        self.interface.load_file += self.__on_load_file
        self.interface.start_clicked += self.__on_start
        self.interface.continue_clicked += self.__on_continue

        self.continue_event = threading.Event()
        self.__on_load_file(file)
        self.machine_thread = None

    def __readfile(self, infile):
        if infile is None:
            return []
        res = []
        f = open(infile, "r")
        gcode = f.readlines()
        if infile != None:
            f.close()
        for l in gcode:
            res.append(l.splitlines()[0])
        return res

    def __load_file(self, name):
        """ Load and parse gcode file """
        parser = GLineParser()
        gcode = self.__readfile(name)
        self.frames = []

        self.interface.clear_commands()

        try:
            for line in gcode:
                frame = parser.parse(line)
                if frame == None:
                    raise Exception("Invalid line")
                self.frames.append(frame)
                self.interface.add_command(line)

            self.machine.load(self.frames)
        except Exception as e:
            print("Except %s" % e)
            self.machine.init()

    def run(self):
        self.interface.run()

    def __on_start(self):
        self.continue_event.clear()
        if self.machine_thread != None:
            self.machine_thread.dispose()
        self.machine_thread = MachineThread(self.machine, self.continue_event)
        self.machine_thread.start()

    def __on_continue(self):
        self.continue_event.set()

    def __on_load_file(self, name):
        """ Load and parse gcode file """
        self.interface.clear_commands()
        self.machine = Machine()
        self.__load_file(name)

def main():
    
    infile = None
    
    try:
        optlist, _ = getopt.getopt(sys.argv[1:], "i:o:h")
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    for o, a in optlist:
        if o == "-i":
            infile = a
        elif o == "-h":
            usage()
            sys.exit(0)

    ctl = Controller(infile)
    ctl.run()
    
if __name__ == "__main__":
    main()
