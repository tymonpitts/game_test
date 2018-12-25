import math

from . import Point, Matrix


class AbstractCamera(object):
    def __init__(self, position=None):
        self._fovy = 45.0
        self._near = 0.01
        self._far = 10000.0

        self._roty = 0.0
        self._rotx = 0.0
        position = position or [0.0, 0.0, 0.0]
        self._pos = Point.cast(position)
        self.matrix = Matrix()

        self.projection_matrix = Matrix()

        self.acceleration_rate = 0.1
        self.rotation_speed = 0.001
        self.max_speed = 0.5

    def reshape(self, w, h):
        self.projection_matrix = self._build_perspective_mat(w, h)

    def _build_perspective_mat(self, w, h):
        aspect = w / float(h)
        frustum_depth = self._far - self._near
        one_over_depth = 1.0 / frustum_depth

        result = Matrix()
        result[1, 1] = 1.0 / math.tan(0.5 * math.radians(self._fovy))
        result[0, 0] = -1.0 * result[1,1] / aspect
        result[2, 2] = self._far * one_over_depth
        result[3, 2] = (-self._far * self._near) * one_over_depth
        result[2, 3] = 1.0
        result[3, 3] = 0.0
        return result

    def clamp_angle(self, angle, clamp=math.pi):
        if abs(angle) > clamp:
            multiplier = -1.0
            if angle < 0.0:
                multiplier = 1.0
            angle += clamp * multiplier
        return angle

    def _get_roty_matrix(self):
        r_sy = math.sin(self._roty)
        r_cy = math.cos(self._roty)
        ry = Matrix()
        ry[0,0] = r_cy
        ry[0,2] = -r_sy
        ry[2,0] = r_sy
        ry[2,2] = r_cy
        return ry

    def _get_rotx_matrix(self):
        r_sx = math.sin(self._rotx)
        r_cx = math.cos(self._rotx)
        rx = Matrix()
        rx[1,1] = r_cx
        rx[1,2] = r_sx
        rx[2,1] = -r_sx
        rx[2,2] = r_cx
        return rx

    def _get_rot_matrix(self):
        rx = self._get_rotx_matrix()
        ry = self._get_roty_matrix()
        return rx * ry

    def update(self, time, delta_time):
        raise NotImplementedError

