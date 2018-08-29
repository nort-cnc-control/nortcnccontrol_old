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

from gui import InterfaceThread
from machine import Machine
from parser import GLineParser
from machinethread import MachineThread
import machinethread

def usage():
    pass

class Controller(object):

    class UI2Machine(threading.Thread):
        def __init__(self, controller):
            threading.Thread.__init__(self)
            self.controller = controller

        def run(self):
            while not self.controller.finish_event.is_set():
                try:
                    uievent = self.controller.uievents.get(timeout=0.5)
                    if uievent == InterfaceThread.UIEvent.Finish:
                        self.controller.finish_event.set()

                    elif uievent == InterfaceThread.UIEvent.Continue:
                        self.controller.continue_event.set()

                    elif uievent == InterfaceThread.UIEvent.Start:
                        self.controller.continue_event.clear()
                        if self.controller.machine_thread != None:
                            self.controller.machine_thread.dispose()
                        self.controller.machine_thread = MachineThread(self.controller.machine,
                                            self.controller.continue_event,
                                            self.controller.finish_event,
                                            self.controller.machine_events)
                        self.controller.machine_thread.start()

                    elif type(uievent) == InterfaceThread.UIEventDialogConfirmed:
                        pass
                        #if type(uievent.reason) == MachineThread.MachineToolEvent:
                        #    self.controller.continue_event.set()
                    elif type(uievent) == InterfaceThread.UIEventLoadFile:
                        self.controller.load_file(uievent.filename)
                except queue.Empty:
                    pass
    
    class Machine2UI(threading.Thread):
        def __init__(self, controller):
            threading.Thread.__init__(self)
            self.controller = controller
        
        def run(self):
            while not self.controller.finish_event.is_set():
                try:
                    mevent = self.controller.machine_events.get(timeout=0.5)

                    if type(mevent) == MachineThread.MachineLineEvent:
                        line = mevent.line
                        self.controller.uicommands.put(InterfaceThread.UICommandActiveLine(line))

                    elif type(mevent) == MachineThread.MachineToolEvent:
                        tool = mevent.tool
                        message = "Insert tool #%i" % tool
                        self.controller.uicommands.put(InterfaceThread.UICommand.ModePaused)
                        self.controller.uicommands.put(InterfaceThread.UICommandShowDialog(message, mevent))

                    elif mevent == MachineThread.MachineEvent.Running:
                        self.controller.uicommands.put(InterfaceThread.UICommand.ModeRun)

                    elif mevent == MachineThread.MachineEvent.Finished:
                        self.controller.uicommands.put(InterfaceThread.UICommand.ModeInitial)
                        self.controller.uicommands.put(InterfaceThread.UICommandShowDialog("Program finished"))
                except queue.Empty:
                    pass

    def __init__(self, file = None):
        self.frames = []

        self.uievents = queue.Queue()
        self.uicommands = queue.Queue()
        self.ui = InterfaceThread(self.uicommands, self.uievents)

        self.finish_event = threading.Event()
        self.continue_event = threading.Event()
        self.load_file(file)
        
        self.machine_events = queue.Queue()
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

        print("load")
        self.uicommands.put(InterfaceThread.UICommand.Clear)

        try:
            for line in gcode:
                frame = parser.parse(line)
                if frame == None:
                    raise Exception("Invalid line")
                self.frames.append(frame)
                self.uicommands.put(InterfaceThread.UICommandAddLine(line))

            self.machine.load(self.frames)
        except Exception as e:
            print("Except %s" % e)
            self.machine.init()

    def run(self):
        self.ui.start()
        self.uicommands.put(InterfaceThread.UICommand.ModeInitial)
        ui2m = self.UI2Machine(self)
        m2ui = self.Machine2UI(self)
        ui2m.start()
        m2ui.start()
        self.finish_event.wait()
        m2ui.join()
        ui2m.join()

    def load_file(self, name):
        """ Load and parse gcode file """
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
