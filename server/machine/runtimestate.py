import euclid3
from .common import config

class RuntimeState(object):
    def __convert_hw(self, hw):
        hwc = euclid3.Vector3(hw["x"], hw["y"], hw["z"])
        if config.X_INVERT:
            hwc.x = -hwc.x
        if config.Y_INVERT:
            hwc.y = -hwc.y
        if config.Z_INVERT:
            hwc.z = -hwc.z
        return hwc

    def __init__(self, hw, glob):
        self.coordinate_system = "G53"
        self.__local_shift = euclid3.Vector3()
        self.update_global_coordinates(hw, glob)

    def update_current_coordinate_system(self, cs, shift=None):
        self.coordinate_system = cs
        if cs == "G53" or shift is None:
            self.__local_shift = euclid3.Vector3()
        else:
            self.__local_shift = shift
        print("LOCAL SHIFT = ", shift)
        self.current_crds = self.global_crds - self.__local_shift

    def update_global_coordinates(self, hw, glob):
        self.hw_crds = euclid3.Vector3(hw["x"], hw["y"], hw["z"])
        self.__hwc_crds = self.__convert_hw(hw)
        self.global_crds = glob
        self.__shift = self.global_crds - self.__hwc_crds

    def update_global_coordinates_x(self, hw, glob):
        self.hw_crds.x = hw
        self.__hwc_crds.x = hw
        if config.X_INVERT:
            self.__hwc_crds.x = -self.__hwc_crds.x
        self.global_crds.x = glob
        self.__shift = self.global_crds - self.__hwc_crds
        self.current_crds = self.global_crds - self.__local_shift

    def update_global_coordinates_y(self, hw, glob):
        self.hw_crds.y = hw
        self.__hwc_crds.y = hw
        if config.Y_INVERT:
            self.__hwc_crds.y = -self.__hwc_crds.y
        self.global_crds.y = glob
        self.__shift = self.global_crds - self.__hwc_crds
        self.current_crds = self.global_crds - self.__local_shift

    def update_global_coordinates_z(self, hw, glob):
        self.hw_crds.z = hw
        self.__hwc_crds.z = hw
        if config.Z_INVERT:
            self.__hwc_crds.z = -self.__hwc_crds.z
        self.global_crds.z = glob
        self.__shift = self.global_crds - self.__hwc_crds
        self.current_crds = self.global_crds - self.__local_shift

    def update_coordinates(self, hw):
        self.hw_crds = euclid3.Vector3(hw["x"], hw["y"], hw["z"])
        self.__hwc_crds = self.__convert_hw(hw)
        self.global_crds = self.__hwc_crds + self.__shift
        self.current_crds = self.global_crds - self.__local_shift
