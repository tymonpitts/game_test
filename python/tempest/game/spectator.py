#! /usr/bin/python
#============================================================================#
#================================================================= IMPORTS ==#
import glfw

from .. import core
from . import GAME


#============================================================================#
#=================================================================== CLASS ==#
class Spectator(core.AbstractCamera):
    def __init__(self, position=None):
        super(Spectator, self).__init__(position)
        self.acceleration_rate = 1.0

    def camera_matrix(self):
        return self.matrix

    def render(self):
        pass

    def update(self, time, delta_time):
        # add mouse_move to rotation values
        #
        self._rotx += GAME.mouse_movement[1]
        self._rotx = self.clamp_angle(self._rotx)
        self._roty -= GAME.mouse_movement[0]
        ry = self._get_roty_matrix()
        rx = self._get_rotx_matrix()

        # add movement
        #
        translate = core.Vector()
        if 'W' in GAME.pressed_keys:
            translate.z += self.acceleration_rate
        if 'S' in GAME.pressed_keys:
            translate.z -= self.acceleration_rate
        if 'A' in GAME.pressed_keys:
            translate.x += self.acceleration_rate
        if 'D' in GAME.pressed_keys:
            translate.x -= self.acceleration_rate
        if ' ' in GAME.pressed_keys:
            translate.y += self.acceleration_rate
        if glfw.KEY_LSHIFT in GAME.pressed_keys:
            translate.y -= self.acceleration_rate
        translate *= delta_time
        translate *= ry
        self._pos += translate

        # resolve xform components to a full matrix
        #
        self.matrix = rx * ry
        for i in xrange(3):
            self.matrix[3, i] = self._pos[i]
