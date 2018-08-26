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

class Interface(object):

    class GCodeRow(object):

        def __init__(self, raw, cmd):
            self.raw = raw
            self.command = cmd

    def __init__(self, machine):
        self.machine = machine
        builder = Gtk.Builder()
        builder.add_from_file("interface.glade")
        self.window = builder.get_object("window")
        self.window.show_all()

        self.window.connect('destroy', Gtk.main_quit)

        self.load_menu = builder.get_object("open")
        self.load_menu.connect('activate', self.__load_menu_event)
        
        

        self.gstore = builder.get_object("gcodeline")
        self.gcodeview = builder.get_object("gcode")
        linecolumn = Gtk.TreeViewColumn("Line", Gtk.CellRendererText(), text=0)
        self.gcodeview.append_column(linecolumn)

        codecolumn = Gtk.TreeViewColumn("Code", Gtk.CellRendererText(), text=1)
        self.gcodeview.append_column(codecolumn)

    def __load_menu_event(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a g-code", self.window,
                                       Gtk.FileChooserAction.OPEN,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        dialog.destroy()

    def load_file(self, name):
        parser = GLineParser()
        gcode = readfile(name)
        self.frames = []

        self.gstore.clear()

        try:
            lnum = 0
            for line in gcode:
                frame = parser.parse(line)
                if frame == None:
                    raise Exception("Invalid line")
                self.frames.append(self.GCodeRow(line, frame))
                self.gstore.append([lnum + 1, line])
                lnum += 1
            self.machine.load([frame.command for frame in self.frames])
        except Exception:
            self.machine.init()

def main():
    conv = Machine()
    interface = Interface(conv)
    
    infile = None

    try:
        optlist,_ = getopt.getopt(sys.argv[1:], "i:o:h")
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

    Gtk.main()

if __name__ == "__main__":
    main()
