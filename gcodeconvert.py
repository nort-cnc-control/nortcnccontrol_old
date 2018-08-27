#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc


from gui import Interface
from machine import Machine
from parser import GLineParser

def usage():
    pass

class Controller(object):

    def __init__(self, file = None):
        self.frames = []
        self.conv = Machine()
        self.interface = Interface()
        self.interface.load_file += self.__on_load_file
        self.interface.start_clicked += self.__on_start
        self.interface.continue_clicked += self.__on_continue
        self.conv.line_selected += self.__line_number
        self.conv.finished += self.__finished
        self.conv.tool_selected += self.__tool_selected
        if file != None:
            self.__on_load_file(file)

    def run(self):
        self.interface.run()

    def __finished(self):
        self.interface.show_ok("G-Code program finished")

    def __tool_selected(self, tool):
        self.interface.show_ok("Insert tool #%i" % tool)

    def __line_number(self, line):
        self.interface.select_line(line)

    def __on_start(self):
        self.conv.start()

    def __on_continue(self):
        self.conv.run()

    def __readfile(self, infile):
        res = []
        if infile is None:
            f = sys.stdin
        else:
            f = open(infile, "r")
        gcode = f.readlines()
        if infile != None:
            f.close()
        for l in gcode:
            res.append(l.splitlines()[0])
        return res

    def __on_load_file(self, name):
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

            self.conv.load(self.frames)
        except Exception as e:
            print("Except %s" % e)
            self.conv.init()

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
