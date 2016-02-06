import random

import glfw
from OpenGL import GL

from .. import data
from .. import core
from .. import shaders

class Game(core.AbstractWindow):
    INSTANCE = None
    """:type: `Game`"""

    def __init__(self):
        super(Game, self).__init__()
        self.title = 'Tempest'

        self.cube = None

        self.shaders = None
        """:type: dict[str, `core.ShaderProgram`]"""

        self.player = None
        self.world = None
        self.block_ids_to_cls = []

    def init(self):
        super(Game, self).init()
        glfw.Disable(glfw.MOUSE_CURSOR)

        self.cube = core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, data.cube.DRAW_METHOD)
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

    def get_block_cls(self, id):
        return self.block_ids_to_cls[id]

    def retrieve_mouse_data(self):
        window_size = glfw.GetWindowSize()
        window_center = [window_size[0] / 2, window_size[1] / 2]

        mouse_pos = [float(p - window_center[i]) / window_center[i] for i,p in enumerate(glfw.GetMousePos())]
        self.mouse_movement = (mouse_pos[0], mouse_pos[1])

        glfw.SetMousePos(*window_center)

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
            light_dir = core.Vector(0.1, 1.0, 0.5)
            light_dir.normalize()
            GL.glUniform4fv(shader.uniforms['dirToLight'], 1, list(light_dir))

        # # draw scene origin cubes
        # #
        # with self.shaders['skin'] as shader:
        #     mat = core.Matrix()
        #     mat.scale(0.1)
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)
        #     self.cube.render()
        #
        #     mat = core.Matrix()
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
        #     mat = core.Matrix()
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
        #     mat = core.Matrix()
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
        glfw.SetMousePos(*window_center)

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

