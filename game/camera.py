#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math

import numpy
import glfw

from ..core import Matrix

#============================================================================#
#=================================================================== CLASS ==#
class Camera(object):
    def __init__(self):
        self._fovy = 45.0
        self._near = 0.01
        self._far = 100.0

        self._rotx = 0.0
        self._model_view_matrix = Matrix()
        self.matrix = Matrix()
        self.model_view_matrix = Matrix()
        self.projection_matrix = Matrix()

        self.movement_speed = 1.0
        self.rotation_speed = 0.001

    def reshape(self, w, h):
        self.projection_matrix = self._build_perspective_mat(w, h)

    def _build_perspective_mat(self, w, h):
        aspect = w / float(h)
        frustumDepth = self._far - self._near
        oneOverDepth = 1.0 / frustumDepth

        result = Matrix()
        result[1,1] = 1.0 / math.tan(0.5 * math.radians(self._fovy))
        result[0,0] = -1.0 * result[1,1] / aspect
        result[2,2] = self._far * oneOverDepth
        result[3,2] = (-self._far * self._near) * oneOverDepth
        result[2,3] = 1.0
        result[3,3] = 0.0
        return result

    def clamp_angle(self, angle, clamp=math.pi):
        if abs(angle) > clamp:
            multiplier = -1.0
            if angle < 0.0:
                multiplier = 1.0
            angle += clamp * multiplier
        return angle

    def handle_input(self, pressed_keys, mouse_move):
        mat = Matrix()
        if 'W' in pressed_keys:
            mat[3,2] += self.movement_speed
        if 'S' in pressed_keys:
            mat[3,2] -= self.movement_speed
        if 'A' in pressed_keys:
            mat[3,0] += self.movement_speed
        if 'D' in pressed_keys:
            mat[3,0] -= self.movement_speed
        if ' ' in pressed_keys:
            mat[3,1] += self.movement_speed
        if glfw.KEY_LSHIFT in pressed_keys:
            mat[3,1] -= self.movement_speed

        # convert mouse_move to rotation matrices
        # 
        self._rotx += mouse_move[1]
        self._rotx = self.clamp_angle(self._rotx)
        r_sx = math.sin(self._rotx)
        r_cx = math.cos(self._rotx)
        rx = Matrix()
        rx[1,1] = r_cx
        rx[1,2] = r_sx
        rx[2,1] = -r_sx
        rx[2,2] = r_cx

        r_sy = math.sin(-mouse_move[0])
        r_cy = math.cos(-mouse_move[0])
        ry = Matrix()
        ry[0,0] = r_cy
        ry[0,2] = -r_sy
        ry[2,0] = r_sy
        ry[2,2] = r_cy

        self._model_view_matrix = ry * mat * self._model_view_matrix
        self.matrix = rx * self._model_view_matrix
        self.model_view_matrix = self.matrix.inverse()

