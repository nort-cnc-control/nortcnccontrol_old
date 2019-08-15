from .actions import action

from .actions import linear
from .actions import helix
from .actions import pause
from .actions import tools
from .actions import spindle
from .actions import program
from .actions import state

from .modals import positioning

from .common import config
from .common import event

import euclid3

class Program(object):

    def __init__(self, table_sender, spindle_sender):
        self.actions = []
        self.index = 0
        self.line = 0
        self.table_sender = table_sender
        self.spindle_sender = spindle_sender
        self.reset_coordinates_ev = event.EventEmitter()
        self.update_current_cs_ev = event.EventEmitter()

    def __add_action(self, action, extra=None):
        self.actions.append((self.index, action, self.line, extra))

    def inc_index(self):
        self.index += 1

    def insert_reset_coordinates(self, x=None, y=None, z=None):
        def crdcb(hw):
            self.reset_coordinates_ev(hw, x, y, z)

        self.__add_action(state.TableCoordinates(sender=self.table_sender, coordinates_cb=crdcb))

    def insert_coordinate_system_change(self, cs, offset):
        def csupdcb(cs, offset):
            self.update_current_cs_ev(cs, offset)

        self.__add_action(state.CurrentCoordinateSystem(csupdcb, cs, offset))

    def insert_unlock(self):
        self.__add_action(action.MCUCmd("M800", sender=self.table_sender))

    def insert_homing(self):
        gz1 = -config.SIZE_Z
        gz2 = 2
        gz3 = -3
        if config.Z_INVERT:
            gz1 *= -1
            gz2 *= -1
            gz3 *= -1
        gx1 = -config.SIZE_X
        gx2 = 2
        gx3 = -3
        if config.X_INVERT:
            gx1 *= -1
            gx2 *= -1
            gx3 *= -1
        gy1 = -config.SIZE_Y
        gy2 = 2
        gy3 = -3
        if config.Y_INVERT:
            gy1 *= -1
            gy2 *= -1
            gy3 *= -1

        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,0,gz1),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,0,gz2),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,0,gz3),
                                                feed=config.PRECISE_FEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(gx1, 0, 0),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(gx2,0,0),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(gx3,0,0),
                                                feed=config.PRECISE_FEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,gy1,0),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,gy2,0),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,gy3,0),
                                                feed=config.PRECISE_FEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(action.MCUCmd("M997", sender=self.table_sender))

    def insert_z_probe(self):
        gz1 = config.SIZE_Z
        gz2 = -2
        gz3 = 3
        if config.Z_INVERT:
            gz1 *= -1
            gz2 *= -1
            gz3 *= -1
        self.__add_action(action.MCUCmd("M996", sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,0,gz1),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,0,gz2),
                                                feed=config.MAXFEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(linear.LinearMovement(delta=euclid3.Vector3(0,0,gz3),
                                                feed=config.PRECISE_FEED,
                                                acc=config.ACCELERATION,
                                                sender=self.table_sender))
        self.__add_action(action.MCUCmd("M998", sender=self.table_sender))
        self.__add_action(action.MCUCmd("M995", sender=self.table_sender))

    #region movements
    def __insert_linear_movement(self, source, target, offset, table_state, feed):
        dir0, dir1 = linear.LinearMovement.find_geometry(source, target)

        move_source = source + offset * dir0
        move_target = target + offset * dir1

        movement = linear.LinearMovement(delta=move_target - move_source,
                                         feed=feed,
                                         acc=table_state.acc,
                                         sender=self.table_sender)

        extra = {
            "source" : source,
            "target" : target,
            "move_source" : move_source,
            "move_target" : move_target,
            "dir0" : dir0,
            "dir1" : dir1,
        }
        self.__add_action(movement, extra)

    def __insert_fast_movement(self, source, target, offset, table_state):
        self.__insert_linear_movement(source, target, offset, table_state, table_state.fastfeed)

    def __insert_payload_movement(self, source, target, offset, table_state):
        self.__insert_linear_movement(source, target, offset, table_state, table_state.feed)

    def __axis_convert(self, axis):
        if axis == positioning.PositioningState.PlaneGroup.xy:
            axis = helix.HelixMovement.Axis.xy
        elif axis == positioning.PositioningState.PlaneGroup.yz:
            axis = helix.HelixMovement.Axis.yz
        else:
            axis = helix.HelixMovement.Axis.zx
        return axis

    def __insert_arc_R(self, source, target, offset, R, table_state):
        ccw = table_state.motion == positioning.PositioningState.MotionGroup.round_ccw
        axis = self.__axis_convert(table_state.plane)

        center, dir0, dir1, arc_angle = helix.HelixMovement.find_geometry(source, target, ccw, axis, r=R)

        print("Center(R) = ", center)
        move_source = source + offset * dir0
        move_target = target + offset * dir1

        movement = helix.HelixMovement(source_to_center=center - move_source,
                                       delta=move_target - move_source,
                                       axis=axis,
                                       ccw=ccw,

                                       feed=table_state.feed,
                                       acc=table_state.acc,
                                       sender=self.table_sender)

        extra = {
            "source" : source,
            "target" : target,
            "move_source" : move_source,
            "move_target" : move_target,
            "dir0" : dir0,
            "dir1" : dir1,
        }
        self.__add_action(movement, extra)

    def __insert_arc_IJK(self, source, target, offset, I, J, K, table_state):
        ccw = table_state.motion == positioning.PositioningState.MotionGroup.round_ccw
        axis = self.__axis_convert(table_state.plane)

        center, dir0, dir1, arc_angle = helix.HelixMovement.find_geometry(source, target, ccw, axis, i=I, j=J, k=K)

        move_source = source + offset * dir0
        move_target = target + offset * dir1
        #print("Offset = ", offset)
        #print("Src = ", move_source)
        #print("Dst = ", move_target)
        print("Center(IJK) = ", center)
        movement = helix.HelixMovement(source_to_center=center - move_source,
                                       delta=move_target - move_source,
                                       axis=axis,
                                       ccw=ccw,

                                       feed=table_state.feed,
                                       acc=table_state.acc,
                                       sender=self.table_sender)

        extra = {
            "source" : source,
            "target" : target,
            "move_source" : move_source,
            "move_target" : move_target,
            "dir0" : dir0,
            "dir1" : dir1,
        }
        self.__add_action(movement, extra)

    def insert_move(self, pos, table_state):
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

        source = table_state.pos
        target = source + delta
        offset = table_state.r_offset_radius

        # Normal linear move
        if table_state.motion == positioning.PositioningState.MotionGroup.line:
            self.__insert_payload_movement(source, target, offset, table_state)

        # Fast linear move
        elif table_state.motion == positioning.PositioningState.MotionGroup.fast_move:
            self.__insert_fast_movement(source, target, offset, table_state)
        
        # Arc movement
        elif table_state.motion == positioning.PositioningState.MotionGroup.round_cw or \
             table_state.motion == positioning.PositioningState.MotionGroup.round_ccw:
            if pos.R != None:
                self.__insert_arc_R(source, target, offset, pos.R, table_state)
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
                self.__insert_arc_IJK(source, target, offset, ci, cj, ck, table_state)

        else:
            raise Exception("Not implemented %s motion state" % table_state.motion)

        return target
    
    def insert_stop(self):
        self.__add_action(pause.Break())

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
        act.performed += cb
        self.__add_action(act)
    #endregion control

    def dispose(self):
        if self.actions != None:
            for act in self.actions:
                act[1].dispose()
        self.actions = None
        self.reset_coordinates_ev.dispose()
        self.update_current_cs_ev.dispose()
