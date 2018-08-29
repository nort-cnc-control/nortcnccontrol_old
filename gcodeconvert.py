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

from gui import Interface
from machine import Machine
from parser import GLineParser
from machinethread import MachineThread
import machinethread

def usage():
    pass

class Controller(object):

    class GtkHelperThread(threading.Thread):
        def __init__(self, queue, finish_event, interface):
            threading.Thread.__init__(self)
            self.queue = queue
            self.finish_event = finish_event
            self.interface = interface

        def __show(self, message):
            self.interface.show_ok(message)
            return False

        def __select_line(self, line):
            self.interface.select_line(line)
            return False

        def run(self):
            while not self.finish_event.is_set():
                try:
                    item = self.queue.get(timeout=0.1)
                except queue.Empty:
                    continue
                if type(item) == machinethread.FinishedEvent:
                    GLib.idle_add(self.__show, "GCode finished")
                elif type(item) == machinethread.LineEvent:
                    GLib.idle_add(self.__select_line, item.line)
                elif type(item) == machinethread.ToolEvent:
                    GLib.idle_add(self.__show, "Please insert tool #%i" % item.tool)

    def __init__(self, file = None):
        self.frames = []
        self.interface = Interface()
        self.interface.load_file += self.__on_load_file
        self.interface.start_clicked += self.__on_start
        self.interface.stop_clicked += self.__on_stop
        self.interface.continue_clicked += self.__on_continue

        self.finish_event = threading.Event()
        self.continue_event = threading.Event()
        self.__on_load_file(file)
        self.machine_thread = None
        self.queue = queue.Queue()
        self.gtkhelper = self.GtkHelperThread(self.queue,
                                              self.finish_event,
                                              self.interface)
        self.gtkhelper.start()

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
        self.finish_event.set()
    # machine events handling


    # interface events handling
    def __on_start(self):
        self.continue_event.clear()
        if self.machine_thread != None:
            self.machine_thread.dispose()
        self.machine_thread = MachineThread(self.machine,
                                            self.continue_event,
                                            self.finish_event,
                                            self.queue)
        self.machine_thread.start()

    def __on_continue(self):
        self.continue_event.set()

    def __on_stop(self):
        pass

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
    sys.exit(0)

if __name__ == "__main__":
    main()
