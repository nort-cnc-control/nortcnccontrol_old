import threading

class MachineThread(threading.Thread):

    def __init__(self, machine, continue_event):
        threading.Thread.__init__(self)
        self.machine = machine
        self.finished = False
        self.continue_event = continue_event
        self.machine.line_selected += self.__line_number
        self.machine.finished += self.__finished
        self.machine.tool_selected += self.__tool_selected

    def dispose(self):
        self.machine.line_selected -= self.__line_number
        self.machine.finished -= self.__finished
        self.machine.tool_selected -= self.__tool_selected
        self.machine = None

    def __line_number(self, line):
        print("line #%i" % line)

    def __finished(self):
        self.finished = True
        print("finished")
        
    def __tool_selected(self, tool):
        print("Tool #%i" % tool)

    def run(self):
        end = self.machine.work_init()
        while not self.finished:
            end = self.machine.work_continue()
            self.finished = end or self.finished
            if not end and not self.finished:
                print("Waiting for continue")
                self.continue_event.wait()
                self.continue_event.clear()
