#!/usr/bin/env python3

#from converter import machine
from converter.machine import Machine
from converter.parser import GLineParser

class Emulator(object):

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

        try:
            for line in gcode:
                print("line %s" % line)
                frame = parser.parse(line)
                if frame == None:
                    raise Exception("Invalid line")
                self.frames.append(frame)

            self.machine.load(self.frames)
        except Exception as e:
            print("Except %s" % e)
            self.machine.init()

    def __init__(self, file):
        self.machine = Machine(None)
        self.__load_file(file)

    def run(self):
        self.machine.emulate()

emulator = Emulator("test.gcode")
