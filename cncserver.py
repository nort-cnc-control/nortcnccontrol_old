#!/usr/bin/env python3

import machine
import machine.machine
import machine.parser

import sender
import sender.emulatorsender

import getopt

class Controller(object):
    def __init__(self):
        self.sender = sender.emulatorsender.EmulatorSender()
        self.machine = machine.machine.Machine(self.sender)
        self.parser = machine.parser.GLineParser()
        self.machine.paused += self.continue_on_pause
        self.machine.finished += self.done

    def continue_on_pause(self, reason):
        print(reason)
        self.machine.work_continue()

    def done(self):
        print("Done")

    def load(self, lines):
        frames = []
        for line in lines:
            frame = self.parser.parse(line)
            frames.append(frame)
        self.machine.load(frames)

    def run(self):
        self.machine.work_start()

ctl = Controller()

f = open("test.gcode")
lines = f.readlines()
f.close()

ctl.load(lines)

ctl.run()
