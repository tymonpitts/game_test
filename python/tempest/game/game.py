import random

import glfw
from OpenGL import GL
from typing import Dict, List, Type, TYPE_CHECKING

from .. import data
import game_core
from .. import shaders

if TYPE_CHECKING:
    from .spectator import Spectator
    from .world import World
    from .blocks import AbstractBlock


class Game(game_core.AbstractWindow):
    INSTANCE = None  # type: Game

    def __init__(self):
        super(Game, self).__init__()
        self.title = 'Tempest'

        self.cube = None  # type: game_core.Mesh
        self.shaders = None  # type: Dict[str, game_core.ShaderProgram]
        self.player = None  # type: Spectator
        self.world = None  # type: World
        self.block_ids_to_cls = []  # type: List[Type[AbstractBlock]]

    def init(self):
        super(Game, self).init()
        glfw.set_input_mode(self.window, glfw.CURSOR, False)

        self.cube = game_core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, data.cube.DRAW_METHOD)
        self.shaders = shaders.init()
        self.register_blocks()

        from .world import World
        self.world = World(self, 128)

        # from .player import Player
        # x=0.5
        # z=-3.5
        # y = self.world.get_height(x,z)
        # self.player = Player(self, [x, y, z])

        from .spectator import Spectator
        x = 0.0
        z = 0.0
        y = 64.0
        self.player = Spectator([x, y, z])

    def register_blocks(self):
        from .blocks import _BLOCKS
        current_id = 0
        for cls in _BLOCKS:
            print 'Registering %s' % cls.__name__
            next_id = cls.register(current_id)
            num_ids = next_id - current_id
            self.block_ids_to_cls.extend([cls] * num_ids)
            current_id = next_id
            print '    registered states: %s' % num_ids

    # noinspection PyShadowingBuiltins
    def get_block_cls(self, id):
        return self.block_ids_to_cls[id]

    def retrieve_mouse_data(self):
        window_size = glfw.get_framebuffer_size(self.window)
        window_center = [window_size[0] / 2, window_size[1] / 2]

        mouse_pos = [float(p - window_center[i]) / window_center[i] for i, p in enumerate(glfw.get_cursor_pos(self.window))]
        self.mouse_movement = (mouse_pos[0], mouse_pos[1])

        glfw.set_cursor_pos(self.window, *window_center)

    def integrate(self, t, delta_time):
        self.retrieve_mouse_data()
        self.player.update(t, delta_time)

    def draw(self):
        random.seed(1121327837)
        i_cam_mat = self.player.camera_matrix().inverse()
        for shader in self.shaders.itervalues():
            if 'worldToCameraMatrix' not in shader.uniforms:
                continue
            with shader:
                GL.glUniformMatrix4fv(shader.uniforms['worldToCameraMatrix'], 1, GL.GL_FALSE, i_cam_mat.tolist())

        with self.shaders['skin'] as shader:
            light_dir = game_core.Vector(0.1, 1.0, 0.5)
            light_dir.normalize()
            GL.glUniform4fv(shader.uniforms['dirToLight'], 1, list(light_dir))

        # # draw scene origin cubes
        # #
        # with self.shaders['skin'] as shader:
        #     mat = game_core.Matrix()
        #     mat.scale(0.1)
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)
        #     self.cube.render()
        #
        #     mat = game_core.Matrix()
        #     mat.scale(0.1)
        #     mat.translate([1,0,0])
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
        #     self.cube.render()
        #
        #     mat = game_core.Matrix()
        #     mat.scale(0.1)
        #     mat.translate([0,1,0])
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 1.0, 0.0, 1.0)
        #     self.cube.render()
        #
        #     mat = game_core.Matrix()
        #     mat.scale(0.1)
        #     mat.translate([0,0,1])
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 0.0, 1.0, 1.0)
        #     self.cube.render()

        self.world.render()
        self.player.render()

    def reshape(self, w, h):
        super(Game, self).reshape(w, h)

        window_center = [w / 2, h / 2]
        glfw.set_cursor_pos(self.window, *window_center)

        self.player.reshape(w, h)

        for shader in self.shaders.itervalues():
            if 'cameraToClipMatrix' not in shader.uniforms:
                continue
            with shader:
                GL.glUniformMatrix4fv(
                    shader.uniforms['cameraToClipMatrix'],
                    1,
                    GL.GL_FALSE,
                    self.player.projection_matrix.tolist(),
                )
