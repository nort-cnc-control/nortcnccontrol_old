#!/usr/bin/python3

import euclid3
import sys
import getopt
import abc
import regex

def usage():
    pass

def readfile(infile):
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

class Action(object):
    @abc.abstractmethod
    def make_code(self):
        pass

class LinearMovement(Action):

    def make_code(self):
        g1 = "G01 F%i P%i L%i T%i " % (self.feed, self.feed0, self.feed1, self.acceleration)
        g2 = "X%.2f Y%.2f Z%.2f" % (self.delta.X, self.delta.Y, self.delta.Z)
        return g1 + g2

    def __init__(self, delta, feed):
        self.delta = delta
        self.feed = feed
        self.feed0 = 0
        self.feed1 = 0
        self.acceleration = 10
        self.feed 
        self.gcode = None

class Machine(object):
    outcode = []
    actions = []
    feed = 1

    def move(self, delta):
        pass

    def generate_control(self):
        for act in self.actions:
            self.outcode.append(act.make_code())



class GCmd(object):

    def __init__(self, s):
        self.parsed = None
        self.type = s[0]
        self.value = s[1:]
        if "GMTF".find(self.type) != -1:
            self.value = int(self.value)
        elif "XYZABC".find(self.type) != -1:
            self.value = float(self.value)

    def __repr__(self):
        return str(self.type) + str(self.value)

class GFrame(object):

    def __init__(self, cmds, comments):
        self.commands = []
        for cmd in cmds:
            self.commands.append(GCmd(cmd))
        self.comments = comments
    
    def __repr__(self):
        res = str(self.commands[0])
        for cmd in self.commands[1:]:
            res += " " + str(cmd)
        return res

class GLineParser(object):
    def __init__(self):
        pattern = r"(?:[ ]*(?:\((.*)\))*[ ]*([A-Z][0-9]*[\.[0-9]*]?))*[ ]*(?:\((.*)\))*[ ]*(?:;(.*))?"
        self.re = regex.compile(pattern)

    def parse(self, line):
        r = self.re.fullmatch(line)
        if r == None:
            return None

        try:
            frame = GFrame(r.captures(2), r.captures(1) + r.captures(3) + r.captures(4))
            return frame
        except:
            return None

def main():
    parser = GLineParser()
    conv = Machine()
    infile = None
    outfile = None

    try:
        optlist,_ = getopt.getopt(sys.argv[1:], "i:o:h")
    except getopt.GetoptError as err:
        print(err)
        sys.exit(1)

    for o, a in optlist:
        if o == "-i":
            infile = a
        elif o == "-o":
            outfile = a
        elif o == "-h":
            usage()
            sys.exit(0)

    gcode = readfile(infile)
    for line in gcode:
        frame = parser.parse(line)
        if frame == None:
            print("Invalid line")
            continue
        print(frame, frame.comments)

if __name__ == "__main__":
    main()
