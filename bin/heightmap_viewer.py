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

        self.depth = 0

        self.texture_quad_vao = None
        """:type: int"""

        self.texture_data = None
        """:type: list[ list[float] ]"""

        self.textures = None
        """:type: list[int]"""

    # def _generate_debug_mesh(self):
    #     info = self.heightmap._get_info()
    #     info['cube'] = data.cube
    #     info['index_offset'] = 0
    #     verts, normals, indices = self.heightmap._root._generate_debug_mesh(info)
    #     self.mesh = core.Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def generate_debug_texture(self):
        info = self.heightmap._get_info()
        self.texture_data = [[0.0 for j in xrange(((2 ** i) ** 2) * 3)] for i in xrange(self.heightmap.max_depth())]
        self.heightmap._root._generate_debug_texture(info, self.texture_data)
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

        self.textures = []
        for i in xrange( self.heightmap.max_depth() ):
            # Create one OpenGL textures
            self.textures.append( GL.glGenTextures(1) )

            # "Bind" the newly created texture : all future texture functions will modify this texture
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.textures[i])

            # Give the image to OpenGL
            array_type = (GL.GLfloat * len(self.texture_data[i]))
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGB,
                2**i,
                2**i,
                0,
                GL.GL_RGB,
                GL.GL_FLOAT,
                array_type(*self.texture_data[i])
            )

            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)

    def init(self):
        super(HeightMapViewer, self).init()
        glfw.Disable(glfw.MOUSE_CURSOR)

        self.shaders = shaders.init()

        # self.heightmap = HeightMap(size=16, max_height=4.0, max_depth=4, seed=1121327837)
        self.heightmap = core.HeightMap(size=256, max_height=128.0, max_depth=8, seed=1121327837)
        # self.heightmap = HeightMap(size=512, max_height=256.0, max_depth=9, seed=1121327837)
        # self.heightmap = HeightMap(size=2097152.0, max_height=8850.0, max_depth=23, seed=1121327837)
        # self.heightmap = HeightMap(size=2097152.0, max_height=100.0, max_depth=23, seed=1121327837)
        # self.heightmap = HeightMap(size=16384.0, max_height=100.0, max_depth=16, seed=1121327837)

        # import cProfile
        # cProfile.run('from tempest.game import Game; Game.INSTANCE.world._generate_all_nodes()')
        # import sys
        # sys.exit(0)
        with Timer('HeightMap generation', log=True):
            # self.heightmap._generate_all_nodes()
            self.heightmap.generate( core.Point() )
            self.generate_debug_texture()
        # self.heightmap._generate_debug_texture()
        # self.heightmap._generate_debug_mesh()

        # from .player import Player
        # x=0.5
        # z=-3.5
        # y = self.heightmap.get_height(x,z)
        # self.player = Player(self, [x, y, z])

    def keyboard_event(self, key, press):
        if press:
            if key == glfw.KEY_DOWN and glfw.KEY_DOWN not in self.pressed_keys:
                self.depth -= 1
                if self.depth < 0:
                    self.depth = 0
            if key == glfw.KEY_UP and glfw.KEY_UP not in self.pressed_keys:
                self.depth += 1
                if self.depth >= len(self.textures):
                    self.depth = len(self.textures) - 1

        super(HeightMapViewer, self).keyboard_event(key, press)

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        with self.shaders['heightmap'] as shader:
            # Bind our texture in Texture Unit 0
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self.textures[self.depth])
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

