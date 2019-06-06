import euclid3

from . import program
from . import arguments

from .modals import positioning
from .modals import tool

class ProgramBuilder(object):
    
    def __init__(self, table_sender, spindel_sender, registers, previous_state=None):
        self.program = program.Program(table_sender, spindel_sender)
        if previous_state is None:
            self.table_state = positioning.PositioningState()
            self.tool_state = tool.ToolState()
        else:
            self.table_state = previous_state[0].copy()
            self.tool_state = previous_state[1].copy()

        self.table_state.tool_diameter = registers["tools"]

        self.__subprograms = {}
        self.program_stack = []
        self.finish_cb = None
        self.tool_select_cb = None
        self.pause_cb = None

    def get_state(self):
        return (self.table_state, self.tool_state)

    #region movement options
    def __set_feed(self, feed):
        if self.table_state.feed_mode != positioning.PositioningState.FeedRateGroup.feed:
            raise Exception("Unsupported feed mode %s" % self.table_state.feed_mode)
        self.table_state.feed = feed
        return None

    def set_acceleration(self, acc):
        self.table_state.acc = acc
        return None
    
    def set_jerk(self, jerk):
        self.table_state.jerk = jerk
        return None
    #endregion movement options

    #region Subprograms
    def __use_subprogram(self, id, frame):
        pr = arguments.ProgramId(frame)
        if pr.program is None:
            print("WARNING: no subprogram Id, ignoring")
            return None

        pid = pr.program
        subprogram = self.__subprograms[pid]

        self.program_stack.append(id + 1)
        # for multiple calling
        for _ in range(pr.num - 1):
            self.program_stack.append(subprogram)

        return subprogram

    def __return_from_subprogramm(self):
        if len(self.program_stack) == 0:
            self.program.insert_program_end(self.finish_cb)
            return -1

        tid = self.program_stack[-1]
        self.program_stack = self.program_stack[:-1]
        return tid
    #endregion

    #region spindle control
    def __start_stop_spindle(self, old, new):
        if old != new:
            if new == self.tool_state.SpindleGroup.spindle_stop:
                self.program.insert_spindle_off()
            elif new == self.tool_state.SpindleGroup.spindle_cw:
                self.program.insert_spindle_on(True, self.tool_state.speed)
            elif new == self.tool_state.SpindleGroup.spindle_ccw:
                self.program.insert_spindle_on(False, self.tool_state.speed)
    #endregion spindle control

    #region coordinate system
    def __set_coordinates(self, x, y, z):
        self.table_state.set_coordinate_system(x, y, z)

    #endregion coordinate system

    #region frame processing
    def __process_begin(self, frame):
        old_state = self.tool_state.spindle
        self.tool_state.process_begin(frame)
        new_state = self.tool_state.spindle

        speed = arguments.SpindleSpeed(frame)

        if speed.speed is not None:            
            if speed.speed != self.tool_state.speed:
                self.program.insert_set_speed(speed.speed)
            self.tool_state.speed = speed.speed

        self.__start_stop_spindle(old_state, new_state)

    def __process_move(self, frame):
        self.table_state.process_frame(frame)
        pos = arguments.Positioning(frame)

        if pos is not None and self.table_state.units is self.table_state.UnitsGroup.inches:
            pos.as_inches()

        feed = arguments.Feed(frame)
        stop = arguments.ExactStop(frame)
        tool = arguments.Tool(frame)
        
        no_motion = False

        for cmd in frame.commands:
            if cmd.type == "G":
                if cmd.value == 74:
                    self.program.insert_homing()
                    self.table_state.pos.x = 0
                    self.table_state.pos.y = 0
                    self.table_state.pos.z = 0
                elif cmd.value == 30:
                    self.program.insert_z_probe()
                    self.table_state.pos.z = 0
                elif cmd.value == 92:
                    # set offset registers
                    self.__set_coordinates(x=pos.X, y=pos.Y, z=pos.Z)
                    no_motion = True
            elif cmd.type == "M":
                if cmd.value == 6 and tool.tool != None:
                    self.program.insert_select_tool(tool.tool, self.tool_select_cb)
                    self.table_state.select_tool(tool.tool)

        if feed.feed != None:
            self.__set_feed(feed.feed)

        if pos.is_moving and not no_motion:
            self.table_state.pos = self.program.insert_move(pos, stop.exact_stop, self.table_state)
            #print("Pos = ", self.table_state.pos)

    def __process_end(self, id, frame):

        old_state = self.tool_state.spindle
        self.tool_state.process_end(frame)
        new_state = self.tool_state.spindle

        self.__start_stop_spindle(old_state, new_state)
        
        for cmd in frame.commands:
            if cmd.type != "M":
                continue
            if cmd.value == 0:
                self.program.insert_pause(self.pause_cb)
            elif cmd.value == 2 or cmd.value == 30:
                self.program.insert_program_end(self.finish_cb)
                return -1
            elif cmd.value == 97:
                return self.__use_subprogram(id, frame)
            elif cmd.value == 99:
                return self.__return_from_subprogramm()
        return None

    def __process(self, id, frame):
        self.program.line = id

        self.line_number = arguments.LineNumber(frame)

        self.__process_begin(frame)
        self.__process_move(frame)
        next = self.__process_end(id, frame)

        self.program.inc_index()
        return next

    def __save_label(self, id, frame):
        pid = arguments.LineNumber(frame)
        if pid.N != None:
            self.__subprograms[pid.N] = id

    def build_program(self, frames):
        for id in range(len(frames)):
            self.__save_label(id, frames[id])

        id = 0
        self.program.insert_unlock()
        while id < len(frames):
            next = self.__process(id, frames[id])
            if next is None:
                id = id + 1
            elif next < 0:
                break
            else:
                id = next
        return self.program

    #endregion frame processing
