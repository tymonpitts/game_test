from OpenGL import GL
from OpenGL.GL import shaders
from OpenGL.GL.ARB import separate_shader_objects, get_program_binary

_TMP_VAO = None
class ShaderProgram(shaders.ShaderProgram):
    """Subclass of OpenGl.GL.shaders.ShaderProgram to extend its functionality

    The __init__ implements a copy of the compileProgram function from OpenGL/GL/shaders.py
    but removes the glDeleteShader calls so shaders can be linked multiple times

    NOTE: originally copied from OpenGL/GL/shaders.py (def compileProgram)
          and removed the glDeleteShader call so shaders can be linked multiple times

    :param args: arbitrary number of shaders to attach to the generated program.
    :keyword separable: set the separable flag to allow for partial
        installation of shader into the pipeline (see glUseProgramStages)
    :keyword retrievable: set the retrievable flag to allow retrieval of
        the program binary representation, (see glProgramBinary, glGetProgramBinary)

    :rtype: `GL.GLuint`
    :returns: ShaderProgram() program reference
    :raises RuntimeError: when a link/validation failure occurs
    """
    def __new__(cls, *args, **kwargs):
        global _TMP_VAO
        if _TMP_VAO is None:
            _TMP_VAO = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(_TMP_VAO)

        self = shaders.ShaderProgram.__new__( cls, GL.glCreateProgram() )
        self.uniforms = {}

        if kwargs.get('separable'):
            GL.glProgramParameteri( self, separate_shader_objects.GL_PROGRAM_SEPARABLE, GL.GL_TRUE )
        if kwargs.get('retrievable'):
            GL.glProgramParameteri( self, get_program_binary.GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL.GL_TRUE )
        for shader in args:
            GL.glAttachShader(self, shader)
        GL.glLinkProgram(self)
        self.check_validate()
        self.check_linked()

        return self

    def store_uniform_location(self, name):
        self.uniforms[name] = GL.glGetUniformLocation(self, name)

    def __enter__(self):
        GL.glUseProgram(self)
        return self

    def __exit__(self, typ, val, tb):
        GL.glUseProgram(0)

