#!/usr/bin/env python3

import euclid3
import sys
import getopt
import abc
import gi
import OpenGL
import OpenGL.GL

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

    def __render_path(self, widget, context, extradata):
        OpenGL.GL.glClearColor (0.1, 0.1, 0.1, 1.0)
        OpenGL.GL.glClear (OpenGL.GL.GL_COLOR_BUFFER_BIT)
        OpenGL.GL.glFlush()
        return True

    def __init__(self, machine):
        self.machine = machine
        builder = Gtk.Builder()
        builder.add_from_file("interface.glade")
        self.window = builder.get_object("window")
        self.window.show_all()

        self.window.connect('destroy', Gtk.main_quit)

        self.load_menu = builder.get_object("open")
        self.load_menu.connect('activate', self.__load_menu_event)
        
        self.glarea = builder.get_object("model")
        self.glarea.connect('render', self.__render_path, None)

        self.gstore = builder.get_object("gcodeline")
        self.gcodeview = builder.get_object("gcode")
        linecolumn = Gtk.TreeViewColumn("Line", Gtk.CellRendererText(), text=0)
        self.gcodeview.append_column(linecolumn)
        codecolumn = Gtk.TreeViewColumn("Code", Gtk.CellRendererText(), text=1)
        self.gcodeview.append_column(codecolumn)

        self.start = builder.get_object("start")
        self.start.connect("clicked", self.__start_program)

        self.cont = builder.get_object("continue")
        self.cont.connect("clicked", self.__continue_program)

    def __select_index(self, index):
        print("index = %i" % index)

    def __start_program(self, widget):
        res = self.machine.start(self.__select_index)
        if res == False:
            print("Paused")
        return True

    def __continue_program(self, widget):
        res = self.machine.run(self.__select_index)
        if res == False:
            print("Paused")
        return True

    def __load_menu_event(self, widget):
        dialog = Gtk.FileChooserDialog("Please choose a g-code", self.window,
                                       Gtk.FileChooserAction.OPEN,
                            (Gtk.STOCK_CANCEL, Gtk.ResponseType.CANCEL,
                             Gtk.STOCK_OPEN, Gtk.ResponseType.OK))
        response = dialog.run()
        if response == Gtk.ResponseType.OK:
            self.load_file(dialog.get_filename())
        dialog.destroy()
        return True

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
        except Exception as e:
            print("Except %s" % e)
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
