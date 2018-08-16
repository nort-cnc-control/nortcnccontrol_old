#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc
from parser import GLineParser
from converter import Machine

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
            break
        conv.process(frame)

    conv.concat_moves()
    conv.generate_control()
    for ctl in conv.outcode:
        print(ctl)


if __name__ == "__main__":
    main()
