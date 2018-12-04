import threading
import enum
import traceback

class MachineThread(threading.Thread):

    class MachineLineEvent(object):
        def __init__(self, line):
            self.line = line

    class MachineToolEvent(object):
        def __init__(self, tool):
            self.tool = tool

    class MachineEvent(enum.Enum):
        Finished = 1
        Running = 2
        Paused = 3

    class MachineEventPaused(object):
        def __init__(self, display):
            self.display = display

    def __init__(self, machine, continue_event, finish_event, machine_events):
        threading.Thread.__init__(self)
        self.machine = machine
        self.finished = False
        self.machine_events = machine_events
        self.disposed = False
        self.continue_event = continue_event
        self.machine.running += self.__m_running
        self.machine.line_selected += self.__line_number
        self.machine.finished += self.__finished
        self.machine.tool_selected += self.__tool_selected
        self.machine.paused += self.__m_paused

    def dispose(self):
        self.machine.line_selected -= self.__line_number
        self.machine.finished -= self.__finished
        self.machine.tool_selected -= self.__tool_selected
        self.machine.paused -= self.__m_paused
        self.machine = None
        self.disposed = True

    def __m_running(self):
        self.machine_events.put(self.MachineEvent.Running)

    def __line_number(self, line):
        self.machine_events.put(self.MachineLineEvent(line))

    def __finished(self):
        self.machine_events.put(self.MachineEvent.Finished)
        self.finished = True

    def __tool_selected(self, tool):
        self.machine_events.put(self.MachineToolEvent(tool))

    def __m_paused(self, display):
        self.machine_events.put(self.MachineEventPaused(display))

    def run(self):
        end = self.machine.work_init()
        while not self.finished:
            if self.disposed:
                return
            end = self.machine.work_continue()
            self.finished = end or self.finished
            if not end and not self.finished:
                print("Waiting for continue")
                self.continue_event.wait()
                self.continue_event.clear()
