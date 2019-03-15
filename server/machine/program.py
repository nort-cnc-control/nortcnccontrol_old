from .actions import action

from .actions import homing
from .actions import linear
from .actions import helix
from .actions import pause
from .actions import tools
from .actions import spindle
from .actions import program

from .modals import positioning

import euclid3

class Program(object):

    def __init__(self, table_sender, spindle_sender):
        self.actions = []
        self.index = 0
        self.line = 0
        self.table_sender = table_sender
        self.spindle_sender = spindle_sender

    def __add_action(self, action):
        self.actions.append((self.index, action, self.line))

    def inc_index(self):
        self.index += 1

    def insert_homing(self, frame):
        self.__add_action(homing.ToBeginMovement(sender=self.table_sender))

    def insert_z_probe(self, frame):
        self.__add_action(homing.ProbeMovement(sender=self.table_sender))

    #region movements
    def __insert_fast_movement(self, delta, exact_stop, table_state):
        movement = linear.LinearMovement(delta, feed=table_state.fastfeed,
                                         acc=table_state.acc,
                                         exact_stop=exact_stop,
                                         sender=self.table_sender)
        self.__add_action(movement)

    def __insert_movement(self, delta, exact_stop, table_state):
        movement = linear.LinearMovement(delta, feed=table_state.feed,
                                         acc=table_state.acc,
                                         exact_stop=exact_stop,
                                         sender=self.table_sender)
        self.__add_action(movement)

    def __axis_convert(self, axis):
        if axis == positioning.PositioningState.PlaneGroup.xy:
            axis = helix.HelixMovement.Axis.xy
        elif axis == positioning.PositioningState.PlaneGroup.yz:
            axis = helix.HelixMovement.Axis.yz
        else:
            axis = helix.HelixMovement.Axis.zx
        return axis

    def __insert_arc_R(self, delta, R, exact_stop, table_state):
        ccw = table_state.motion == positioning.PositioningState.MotionGroup.round_ccw
        axis = self.__axis_convert(table_state.plane)
        movement = helix.HelixMovement(delta, feed=table_state.feed, r=R,
                                       axis=axis, ccw=ccw,
                                       acc=table_state.acc,
                                       exact_stop=exact_stop,
                                       sender=self.table_sender)
        self.__add_action(movement)

    def __insert_arc_IJK(self, delta, I, J, K, exact_stop, table_state):
        ccw = table_state.motion == positioning.PositioningState.MotionGroup.round_ccw
        axis = self.__axis_convert(table_state.plane)
        movement = helix.HelixMovement(delta, feed=table_state.feed, i=I, j=J, k=K,
                                       axis=axis, ccw=ccw,
                                       acc=table_state.acc,
                                       exact_stop=exact_stop,
                                       sender=self.table_sender)
        self.__add_action(movement)

    def insert_move(self, pos, exact_stop, table_state):
        """
        
        """
        print("*** Insert move ", pos.X, pos.Y, pos.Z)
        #traceback.print_stack()
        #print(table_state.positioning)
        if table_state.positioning == positioning.PositioningState.PositioningGroup.absolute:
            cs = table_state.offsets[table_state.coord_system]

            origpos = table_state.pos
            origpos = cs.global2local(origpos.x, origpos.y, origpos.z)
            newpos = origpos

            if pos.X != None:
                newpos = euclid3.Vector3(pos.X, newpos.y, newpos.z)
            if pos.Y != None:
                newpos = euclid3.Vector3(newpos.x, pos.Y, newpos.z)
            if pos.Z != None:
                newpos = euclid3.Vector3(newpos.x, newpos.y, pos.Z)

            delta = newpos - origpos
        else:
            delta = euclid3.Vector3()
            if pos.X != None:
                delta.x = pos.X
            if pos.Y != None:
                delta.y = pos.Y
            if pos.Z != None:
                delta.z = pos.Z

        # Normal linear move
        if table_state.motion == positioning.PositioningState.MotionGroup.line:
            self.__insert_movement(delta, exact_stop, table_state)

        # Fast linear move
        elif table_state.motion == positioning.PositioningState.MotionGroup.fast_move:
            self.__insert_fast_movement(delta, exact_stop, table_state)
        
        # Arc movement
        elif table_state.motion == positioning.PositioningState.MotionGroup.round_cw or \
             table_state.motion == positioning.PositioningState.MotionGroup.round_ccw:
            if pos.R != None:
                self.__insert_arc_R(delta, pos.R, exact_stop, table_state)
            else:
                ci = 0
                cj = 0
                ck = 0
                if pos.I != None:
                    ci = pos.I
                if pos.J != None:
                    cj = pos.J
                if pos.K != None:
                    ck = pos.K
                self.__insert_arc_IJK(delta, ci, cj, ck, exact_stop, table_state)

        else:
            raise Exception("Not implemented %s motion state" % table_state.motion)

        return (table_state.pos + delta)
    
    #endregion movements

    #region Spindle actions
    def insert_set_speed(self, speed):
        self.__add_action(spindle.SpindleSetSpeed(self.spindle_sender, speed))
    
    def insert_spindle_on(self, cw, speed):
        self.__add_action(spindle.SpindleOn(self.spindle_sender, speed, cw))

    def insert_spindle_off(self):
        self.__add_action(spindle.SpindleOff(self.spindle_sender))
    #endregion Tool actions

    #region control
    def insert_pause(self, cb):
        p = pause.WaitResume()
        p.paused += cb
        self.__add_action(p)

    def insert_select_tool(self, tool, cb):
        tl = tools.WaitTool(tool)
        tl.tool_changed += cb
        self.__add_action(tl)

    def insert_program_end(self, cb):
        act = program.Finish()
        act.finished += cb
        self.__add_action(act)
    #endregion control
