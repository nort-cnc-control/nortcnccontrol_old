import event
import threading
import queue
import enum

import gi
import OpenGL
import OpenGL.GL

gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

class Interface(object):    

    def __render_path(self, widget, context, extradata):
        OpenGL.GL.glClearColor(0.1, 0.1, 0.1, 1.0)
        OpenGL.GL.glClear(OpenGL.GL.GL_COLOR_BUFFER_BIT)
        OpenGL.GL.glFlush()
        return True

    def __init__(self):
        self.load_file        = event.EventEmitter()
        self.start_clicked    = event.EventEmitter()
        self.continue_clicked = event.EventEmitter()
        self.pause_clicked    = event.EventEmitter()
        self.stop_clicked     = event.EventEmitter()

        builder = Gtk.Builder()
        builder.add_from_file("interface.glade")
        self.window = builder.get_object("window")
        self.window.show_all()

        self.window.connect('destroy', Gtk.main_quit)

        load_menu = builder.get_object("open")
        load_menu.connect('activate', self.__load_menu_event)

        self.glarea = builder.get_object("model")
        self.glarea.connect('render', self.__render_path, None)

        self.gstore = builder.get_object("gcodeline")
        self.gcodeview = builder.get_object("gcode")
        linecolumn = Gtk.TreeViewColumn("Line", Gtk.CellRendererText(), text=0)
        self.gcodeview.append_column(linecolumn)
        codecolumn = Gtk.TreeViewColumn("Code", Gtk.CellRendererText(), text=1)
        self.gcodeview.append_column(codecolumn)

        self.pause_btn = builder.get_object("pause")
        self.pause_btn.connect("clicked", self.__pause_program)

        self.start_btn = builder.get_object("start")
        self.start_btn.connect("clicked", self.__start_program)

        self.continue_btn = builder.get_object("continue")
        self.continue_btn.connect("clicked", self.__continue_program)

        self.stop_btn = builder.get_object("stop")
        self.stop_btn.connect("clicked", self.__stop_program)

        self.clear_commands()

    def __start_program(self, widget):
        self.start_clicked()
    
    def __continue_program(self, widget):
        self.continue_clicked()

    def __stop_program(self, widget):
        self.stop_clicked()
    
    def __pause_program(self, widget):
        self.pause_clicked()

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
    
    def clear_commands(self):
        self.gstore.clear()
        self.id = 1

    def add_command(self, line):
        self.gstore.append([self.id, line])
        self.id += 1

    def show_ok(self, text):
        dialog = Gtk.MessageDialog(self.window, 0, Gtk.MessageType.INFO,
            Gtk.ButtonsType.OK, "OK")
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()

    def select_line(self, line):
        path = Gtk.TreePath(line)
        selection = self.gcodeview.get_selection()
        selection.select_path(path)

    def switch_to_initial_mode(self):
        self.start_btn.set_sensitive(True)
        self.continue_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(False)
        self.pause_btn.set_sensitive(False)

    def switch_to_paused_mode(self):
        self.start_btn.set_sensitive(False)
        self.continue_btn.set_sensitive(True)
        self.stop_btn.set_sensitive(True)
        self.pause_btn.set_sensitive(False)

    def switch_to_running_mode(self):
        self.start_btn.set_sensitive(False)
        self.continue_btn.set_sensitive(False)
        self.stop_btn.set_sensitive(True)
        self.pause_btn.set_sensitive(True)

    def run(self):
        Gtk.main()

class InterfaceThread(threading.Thread):

    class UIEvent(enum.Enum):
        Finish = 0
        Start = 1
        Stop = 2
        Pause = 3
        Continue = 4

    class UIEventDialogConfirmed(object):
        pass

    class UICommand(object):
        Finish = 0
        ModeInitial = 1
        ModeRun = 2
        ModePaused = 3
        Clear = 4

    class UICommandShowDialog(object):
        def __init__(self, message):
            self.message = message

    class UICommandActiveLine(object):
        def __init__(self, line):
            self.line = line

    class UICommandAddLine(object):
        def __init__(self, command):
            self.command = command

    def __init__(self, commands, events):
        threading.Thread.__init__(self)
        self.commands = commands
        self.events = events
        self.ui = Interface()
        self.ui.start_clicked += self.__emit_start
        self.ui.stop_clicked += self.__emit_stop
        self.ui.pause_clicked += self.__emit_pause
        self.ui.continue_clicked += self.__emit_continue

    def __emit_start(self):
        self.events.put(self.UIEvent.Start)

    def __emit_stop(self):
        self.events.put(self.UIEvent.Stop)
    
    def __emit_pause(self):
        self.events.put(self.UIEvent.Pause)
    
    def __emit_continue(self):
        self.events.put(self.UIEvent.Continue)

    def __check_queue(self):
        try:
            item = self.commands.get_nowait()
        except queue.Empty:
            return True

        if item == self.UICommand.Finish:
            Gtk.main_quit()
        elif item == self.UICommand.ModeInitial:
            self.ui.switch_to_initial_mode()
        elif item == self.UICommand.ModePaused:
            self.ui.switch_to_paused_mode()
        elif item == self.UICommand.ModeRun:
            self.ui.switch_to_running_mode()
        elif item == self.UICommand.Clear:
            self.ui.clear_commands()
        elif type(item) == self.UICommandShowDialog:
            self.ui.show_ok(item.message)
            self.events.put(self.UIEventDialogConfirmed())
        elif type(item) == self.UICommandActiveLine:
            self.ui.select_line(item.line)
        elif type(item) == self.UICommandAddLine:
            self.ui.add_command(item.command)
        return True

    def run(self):
        GLib.idle_add(self.__check_queue)
        self.ui.run()
        self.events.put(self.UIEvent.Finish)
