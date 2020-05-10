#! /usr/bin/python
from __future__ import print_function, division

from typing import Dict

import game_core
import glfw
import healpy
from OpenGL import GL

from .camera import Camera
from .planet import Planet


class Window(game_core.AbstractWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.title = 'Planet Test'
        self.camera = None  # type: Camera
        self.shaders = {}  # type: Dict[str, game_core.shaders.ShaderProgram]
        self.planet = None  # type: Planet
        self.light_direction = None  # type: game_core.Vector

    def init(self):
        super(Window, self).init()

        # hide the cursor and lock it to this window. GLFW will then take care
        # of all the details of cursor re-centering and offset calculation and
        # providing the application with a virtual cursor position
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        self.inspection_index = 0

        self.camera = Camera(position=[0.0, 32.0, 128.0])
        self.camera.init(*glfw.get_framebuffer_size(self.window))
        self._set_perspective_matrix()

        self.planet = Planet(circumference=100.0, chunk_height=10.0)
        self.planet.init()
        self.font = game_core.Font(size=48)

    def _set_perspective_matrix(self):
        # TODO: move this to camera's reshape
        projection_matrix = self.camera.projection_matrix.tolist()
        for shader in game_core.shaders.REGISTRY.values():
            if 'camera_to_clip_matrix' in shader.uniforms:
                with shader:
                    shader.set_uniform(
                        'camera_to_clip_matrix',
                        1,
                        GL.GL_FALSE,
                        projection_matrix,
                    )

    def reshape(self, w, h):
        super(Window, self).reshape(w, h)
        self.camera.reshape(w, h)
        self._set_perspective_matrix()

    def integrate(self, t, delta_time):
        # FOR DEBUGGING
        inspection_index_changed = False
        if glfw.KEY_UP in self.new_pressed_keys:
            self.inspection_index += 1
            self.inspection_index = min(self.inspection_index, healpy.nside2npix(1))
            inspection_index_changed = True
        if glfw.KEY_DOWN in self.new_pressed_keys:
            self.inspection_index -= 1
            self.inspection_index = max(self.inspection_index, 0)
            inspection_index_changed = True
        if inspection_index_changed:
            print('inspection index: {}'.format(self.inspection_index))
            neighbors = healpy.get_all_neighbours(1, self.inspection_index)
            print('  south west: {}'.format(neighbors[0]))
            print('  west:       {}'.format(neighbors[1]))
            print('  north west: {}'.format(neighbors[2]))
            print('  north:      {}'.format(neighbors[3]))
            print('  north east: {}'.format(neighbors[4]))
            print('  east:       {}'.format(neighbors[5]))
            print('  south east: {}'.format(neighbors[6]))
            print('  south:      {}'.format(neighbors[7]))

        self.camera.integrate(t, delta_time, self)

        # TODO: move this to camera's integrate
        i_cam_mat = self.camera.matrix.inverse().tolist()
        for shader in game_core.shaders.REGISTRY.values():
            if 'world_to_camera_matrix' in shader.uniforms:
                with shader:
                    shader.set_uniform(
                        'world_to_camera_matrix',
                        1,
                        GL.GL_FALSE,
                        i_cam_mat
                    )

    def draw(self):
        self.planet.draw(window=self)
