from typing import Tuple, TYPE_CHECKING

import glfw
import game_core

if TYPE_CHECKING:
    # guarded imports to prevent circular dependencies
    from .window import Window


class Camera(game_core.AbstractCamera):
    def __init__(self, position=None):
        super(Camera, self).__init__(position)
        self.acceleration_rate = 10.0
        self.max_speed = 10.0

        # store the last position of the cursor so we can compute how far
        # the cursor moved since the last time we integrated. This will
        # allow us to determine how much to rotate the camera.
        self._last_cursor_position = None  # type: Tuple[float, float]

    def integrate(self, time, delta_time, window):
        # type: (float, float, Window) -> None

        # determine how far the cursor has moved since the last time
        # we integrated. Store the new cursor position so we can do this
        # again next time we integrate.
        cursor_position = glfw.get_cursor_pos(window.window)
        if self._last_cursor_position is None:
            cursor_movement = (0.0, 0.0)
            self._last_cursor_position = cursor_position
        else:
            cursor_movement = (
                cursor_position[0] - self._last_cursor_position[0],
                cursor_position[1] - self._last_cursor_position[1],
            )
            self._last_cursor_position = cursor_position

        # turn the cursor movement into rotational values
        self._rotx -= cursor_movement[1] * 0.01
        self._rotx = self.clamp_angle(self._rotx)
        self._roty -= cursor_movement[0] * 0.01
        ry = self._get_roty_matrix()
        rx = self._get_rotx_matrix()

        # turn key presses into translation values and add that translation
        # to this camera's world position
        translate = game_core.Vector()
        if glfw.KEY_W in window.pressed_keys:
            translate.z -= self.acceleration_rate
        if glfw.KEY_S in window.pressed_keys:
            translate.z += self.acceleration_rate
        if glfw.KEY_A in window.pressed_keys:
            translate.x -= self.acceleration_rate
        if glfw.KEY_D in window.pressed_keys:
            translate.x += self.acceleration_rate
        if glfw.KEY_SPACE in window.pressed_keys:
            translate.y += self.acceleration_rate
        if glfw.KEY_LEFT_SHIFT in window.pressed_keys:
            translate.y -= self.acceleration_rate
        translate *= delta_time
        translate *= ry
        self._pos += translate

        # resolve orientation and position components to a full matrix
        self.matrix = rx * ry
        for i in xrange(3):
            self.matrix[3, i] = self._pos[i]
