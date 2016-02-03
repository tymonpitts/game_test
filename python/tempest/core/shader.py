from OpenGL import GL
from OpenGL.GL.shaders import compileProgram

_TMP_VAO = None
class Shader(object):
    _TMP_VAO = None
    def __init__(self, vertex_shader, fragment_shader):
        global _TMP_VAO
        if _TMP_VAO is None:
            _TMP_VAO = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(_TMP_VAO)

        self.program = compileProgram(vertex_shader, fragment_shader)
        self.uniforms = {}

    def store_uniform_location(self, name):
        self.uniforms[name] = GL.glGetUniformLocation(self.program, name)

    def __enter__(self):
        GL.glUseProgram(self.program)
        return self

    def __exit__(self, typ, val, tb):
        GL.glUseProgram(0)

