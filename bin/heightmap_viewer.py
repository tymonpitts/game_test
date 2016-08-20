#! /usr/bin/python
import glfw
from OpenGL import GL

from tempest import data
from tempest import core
from tempest import shaders
from tempest.core.utils.timer import Timer

class HeightMapViewer(core.AbstractWindow):
    INSTANCE = None
    """:type: `HeightMapViewer`"""

    def __init__(self):
        super(HeightMapViewer, self).__init__()
        self.title = 'HeightMap Viewer'

        self.shaders = None
        """:type: dict[str, `core.ShaderProgram`]"""

        self.heightmap = None
        """:type: `core.HeightMap`"""

        self.texture_quad_vao = None
        """:type: int"""

        self.texture = None
        """:type: list[int]"""

        self.initialized = False
        self.center = core.Point()

    # def _generate_debug_mesh(self):
    #     info = self.heightmap._get_info()
    #     info['cube'] = data.cube
    #     info['index_offset'] = 0
    #     verts, normals, indices = self.heightmap._root._generate_debug_mesh(info)
    #     self.mesh = core.Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def create_texture_vao(self):
        verts = [
            -1.0,  1.0, 0.0,
             1.0,  1.0, 0.0,
             1.0, -1.0, 0.0,
            -1.0, -1.0, 0.0,
        ]
        uvs = [
            0.0, 1.0,
            1.0, 1.0,
            1.0, 0.0,
            0.0, 0.0,
        ]

        self.texture_quad_vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.texture_quad_vao)

        # generate vertex position buffer
        #
        vertexBufferObject = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertexBufferObject)

        array_type = (GL.GLfloat*len(verts))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(verts)*core.FLOAT_SIZE,
            array_type(*verts),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(
            0,              # attribute 0. No particular reason for 0, but must match the layout in the shader.
            3,              # size
            GL.GL_FLOAT,    # type
            GL.GL_FALSE,    # normalized?
            0,              # stride (offset from start of data)
            None            # array buffer offset
        )

        # generate vertex uv buffer
        #
        uvBufferObject = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, uvBufferObject)

        array_type = (GL.GLfloat*len(uvs))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(uvs)*core.FLOAT_SIZE,
            array_type(*uvs),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(
            1,              # attribute 1. No particular reason for 1, but must match the layout in the shader.
            2,              # size
            GL.GL_FLOAT,    # type
            GL.GL_FALSE,    # normalized?
            0,              # stride (offset from start of data)
            None            # array buffer offset
        )

        GL.glBindVertexArray(0)

    def generate_texture(self, width, height):
        data = [1.0, 0.0, 0.0] * (width * height)
        half_viewport_size = core.Point(width / 2.0 * self.heightmap.min_size, height / 2.0 * self.heightmap.min_size)
        viewport = core.BoundingBox2D(self.center - half_viewport_size, self.center + half_viewport_size)
        self.heightmap._generate_debug_texture(viewport, width, height, data)

        if self.texture_quad_vao is None:
            self.create_texture_vao()

        if self.texture is None:
            self.texture = GL.glGenTextures(1)
        # "Bind" the newly created texture : all future texture functions will modify this texture
        GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)

        # Give the image to OpenGL
        array_type = (GL.GLfloat * len(data))
        GL.glTexImage2D(
            GL.GL_TEXTURE_2D,
            0,
            GL.GL_RGB,
            width,
            height,
            0,
            GL.GL_RGB,
            GL.GL_FLOAT,
            array_type(*data)
        )

        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)

    def init(self):
        super(HeightMapViewer, self).init()
        # glfw.Disable(glfw.MOUSE_CURSOR)

        self.shaders = shaders.init()

        # self.heightmap = core.HeightMap(size=16, max_height=4.0, max_depth=4, seed=1121327837)
        # self.heightmap = core.HeightMap(size=256, max_height=128.0, max_depth=8, seed=1121327837)
        self.heightmap = core.HeightMap(size=512, max_height=256.0, max_depth=9, seed=1121327837)
        # self.heightmap = core.HeightMap(size=2097152.0, max_height=8850.0, max_depth=23, seed=1121327837)
        # self.heightmap = core.HeightMap(size=2097152.0, max_height=100.0, max_depth=23, seed=1121327837)
        # self.heightmap = core.HeightMap(size=16384.0, max_height=100.0, max_depth=16, seed=1121327837)

        # import cProfile
        # cProfile.run('from tempest.game import Game; Game.INSTANCE.world._generate_all_nodes()')
        # import sys
        # sys.exit(0)
        with Timer('HeightMap.generate()', log=True):
            # self.heightmap._generate_all_nodes()
            self.heightmap.generate( core.Point() )
            # half_viewport_size = core.Point(self.initial_width / 2.0 * self.heightmap.min_size, self.initial_height / 2 * self.heightmap.min_size)
            # viewport = core.BoundingBox2D(self.center - half_viewport_size, self.center + half_viewport_size)
            # self.heightmap.generate_area(viewport)
        with Timer('generate texture', log=True):
            self.generate_texture(self.initial_width, self.initial_height)
        # self.heightmap._generate_debug_texture()
        # self.heightmap._generate_debug_mesh()

        # from .player import Player
        # x=0.5
        # z=-3.5
        # y = self.heightmap.get_height(x,z)
        # self.player = Player(self, [x, y, z])

    def mouse_button_event(self, button, action):
        """Called when a mouse button is pressed or released

        :param int button: The pressed/released mouse button
        :param int action: GLFW_PRESS or GLFW_RELEASE
        """
        if button == glfw.MOUSE_BUTTON_LEFT and action == glfw.GLFW_PRESS:
            width, height = glfw.GetWindowSize()
            x, y = glfw.GetMousePos()  # integer positions relative to the upper left corner of the window
            x = x - (width / 2)
            y = (height / 2) - y
            self.heightmap.generate( core.Point(x, y) )
            self.generate_texture(width, height)

    def reshape(self, w, h):
        super(HeightMapViewer, self).reshape(w, h)
        if self.initialized:
            self.generate_texture(w, h)

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        with self.shaders['heightmap'] as shader:
            # Bind our texture in Texture Unit 0
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
            # Set our "myTextureSampler" sampler to user Texture Unit 0
            GL.glUniform1i(shader.uniforms['textureSampler'], 0)

            GL.glBindVertexArray(self.texture_quad_vao)
            GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 4)  # Starting from vertex 0; 4 vertices total -> 2 triangles
            GL.glBindVertexArray(0)

        # from OpenGL import GL
        # from ..game import Game
        # from . import Matrix
        # with Game.INSTANCE.shaders['skin'] as shader:
        #     GL.glUniformMatrix4fv(
        #         shader.uniforms['modelToWorldMatrix'],
        #         1,
        #         GL.GL_FALSE,
        #         Matrix().tolist(),
        #     )
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 1.0, 0.5, 1.0)
        #     self.mesh.render()

if __name__ == '__main__':
    HeightMapViewer().run()

