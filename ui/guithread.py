import threading
import enum
import queue

import gi
gi.require_version("Gtk", "3.0")
from gi.repository import Gtk, GLib

from . import gui

class InterfaceThread(threading.Thread):
    
    class QueueHelperThread(threading.Thread):

        def __init__(self, ift):
            threading.Thread.__init__(self)
            self.ift = ift

        def __handle(self, item):
            if item == self.ift.UICommand.Finish:
                Gtk.main_quit()
                self.ift.finish_event.set()

            elif item == self.ift.UICommand.ModeInitial:
                self.ift.ui.switch_to_initial_mode()

            elif item == self.ift.UICommand.ModePaused:
                self.ift.ui.switch_to_paused_mode()

            elif item == self.ift.UICommand.ModeRun:
                self.ift.ui.switch_to_running_mode()

            elif item == self.ift.UICommand.Clear:
                self.ift.ui.clear_commands()

            elif type(item) == self.ift.UICommandShowDialog:
                self.ift.ui.show_ok(item.message)
                notice = self.ift.UIEventDialogConfirmed(item.event)
                self.ift.events.put(notice)

            elif type(item) == self.ift.UICommandActiveLine:
                self.ift.ui.select_line(item.line)

            elif type(item) == self.ift.UICommandAddLine:
                self.ift.ui.add_command(item.command)
            return False

        def run(self):
            while not self.ift.finish_event.is_set():
                try:
                    item = self.ift.commands.get(timeout=0.2)
                    GLib.idle_add(self.__handle, item)
                except queue.Empty:
                    pass
            

    class UIEvent(enum.Enum):
        Finish = 0
        Start = 1
        Stop = 2
        Pause = 3
        Continue = 4

    class UIEventDialogConfirmed(object):
        def __init__(self, reason=None):
            self.reason = reason

    class UIEventLoadFile(object):
        def __init__(self, name):
            self.filename = name

    class UICommand(object):
        Finish = 0
        ModeInitial = 1
        ModeRun = 2
        ModePaused = 3
        Clear = 4

    class UICommandShowDialog(object):
        def __init__(self, message, event=None):
            self.message = message
            self.event = event

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
        self.finish_event = threading.Event()
        self.ui = gui.Interface()
        self.ui.start_clicked += self.__emit_start
        self.ui.stop_clicked += self.__emit_stop
        self.ui.pause_clicked += self.__emit_pause
        self.ui.continue_clicked += self.__emit_continue
        self.ui.load_file += self.__emit_load_file

    def __emit_start(self):
        self.events.put(self.UIEvent.Start)

    def __emit_stop(self):
        self.events.put(self.UIEvent.Stop)
    
    def __emit_pause(self):
        self.events.put(self.UIEvent.Pause)

    def __emit_continue(self):
        self.events.put(self.UIEvent.Continue)

    def __emit_load_file(self, name):
        self.events.put(self.UIEventLoadFile(name))

    def run(self):
        helper = self.QueueHelperThread(self)
        helper.start()
        self.ui.run()
        self.events.put(self.UIEvent.Finish)
        self.finish_event.set()
        helper.join()
