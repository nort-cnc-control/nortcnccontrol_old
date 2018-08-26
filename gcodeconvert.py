#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc
import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk

from parser import GLineParser
from machine import Machine

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

#    builder = Gtk.Builder()
#    builder.add_from_file("interface.glade")

#    window = builder.get_object("window")
#    window.show_all()

#    Gtk.main()

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
    frames = []
    for line in gcode:
        frame = parser.parse(line)
        if frame == None:
            print("Invalid line")
            return
        frames.append(frame)

    conv.load(frames)

    conv.run()

if __name__ == "__main__":
    main()
