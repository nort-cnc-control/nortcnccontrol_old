#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc

from gui import Interface
from machine import Machine

def usage():
    pass


def main():
    conv = Machine()
    interface = Interface(conv)
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

    if infile != None:
        interface.load_file(infile)

    interface.run()

if __name__ == "__main__":
    main()
