import threading

class MachineEvent(object):
    pass

class LineEvent(MachineEvent):

    def __init__(self, line):
        MachineEvent.__init__(self)
        self.line = line

class ToolEvent(MachineEvent):

    def __init__(self, tool):
        MachineEvent.__init__(self)
        self.tool = tool

class FinishedEvent(object):
    pass

class StartedEvent(object):
    pass

class MachineThread(threading.Thread):

    def __init__(self, machine, continue_event, finish_event, queue):
        threading.Thread.__init__(self)
        self.machine = machine
        self.finished = False
        self.queue = queue
        self.disposed = False
        self.continue_event = continue_event
        self.machine.started += self.__m_started
        self.machine.line_selected += self.__line_number
        self.machine.finished += self.__finished
        self.machine.tool_selected += self.__tool_selected

    def dispose(self):
        self.machine.line_selected -= self.__line_number
        self.machine.finished -= self.__finished
        self.machine.tool_selected -= self.__tool_selected
        self.machine = None
        self.disposed = True

    def __m_started(self):
        self.queue.put(StartedEvent())

    def __line_number(self, line):
        self.queue.put(LineEvent(line))

    def __finished(self):
        self.queue.put(FinishedEvent())
        self.finished = True

    def __tool_selected(self, tool):
        self.queue.put(ToolEvent(tool))

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
