from OpenGL import GL
from . import SHORT_SIZE, FLOAT_SIZE

class Mesh(object):
    def __init__(self, vertices, normals, indices, draw_method):
        self.draw_method = draw_method
        self.indices = indices

        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)

        vertexBufferObject = GL.glGenBuffers(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertexBufferObject)
        data = vertices + normals
        array_type = (GL.GLfloat*len(data))
        GL.glBufferData(
                GL.GL_ARRAY_BUFFER,
                len(data)*FLOAT_SIZE,
                array_type(*data),
                GL.GL_STATIC_DRAW)
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(vertices)*FLOAT_SIZE))

        indexBufferObject = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, indexBufferObject)
        array_type = (GL.GLuint*len(self.indices))
        GL.glBufferData(
                GL.GL_ELEMENT_ARRAY_BUFFER,
                len(self.indices)*FLOAT_SIZE,
                array_type(*self.indices),
                GL.GL_STATIC_DRAW)

        GL.glBindVertexArray(0)

    def render(self):
        GL.glBindVertexArray(self.vao)
        GL.glDrawElements(self.draw_method, len(self.indices), GL.GL_UNSIGNED_INT, None)
        GL.glBindVertexArray(0)
