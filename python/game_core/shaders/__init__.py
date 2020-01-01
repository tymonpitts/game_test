from collections import OrderedDict
import glob
import os
import re

from OpenGL import GL
from OpenGL.GL.ARB import separate_shader_objects, get_program_binary
import OpenGL.GL.shaders
from typing import Dict


REGISTRY = OrderedDict()  # type: Dict[str, ShaderProgram]
CONSTANT = None  # type: ShaderProgram
POINT = None  # type: ShaderProgram
SURFACE = None  # type: ShaderProgram
TEXT_3D = None  # type: ShaderProgram
_TMP_VAO = None
_UNIFORM_TYPE_TO_SETTER = {
    GL.GL_FLOAT: GL.glUniform1f,
    GL.GL_FLOAT_VEC2: GL.glUniform2f,
    GL.GL_FLOAT_VEC3: GL.glUniform3f,
    GL.GL_FLOAT_VEC4: GL.glUniform4f,
    GL.GL_DOUBLE: GL.glUniform1d,
    GL.GL_DOUBLE_VEC2: GL.glUniform2d,
    GL.GL_DOUBLE_VEC3: GL.glUniform3d,
    GL.GL_DOUBLE_VEC4: GL.glUniform4d,
    GL.GL_INT: GL.glUniform1i,
    GL.GL_INT_VEC2: GL.glUniform2i,
    GL.GL_INT_VEC3: GL.glUniform3i,
    GL.GL_INT_VEC4: GL.glUniform4i,
    GL.GL_UNSIGNED_INT: GL.glUniform1ui,
    GL.GL_UNSIGNED_INT_VEC2: GL.glUniform2ui,
    GL.GL_UNSIGNED_INT_VEC3: GL.glUniform3ui,
    GL.GL_UNSIGNED_INT_VEC4: GL.glUniform4ui,
    GL.GL_BOOL: GL.glUniform1i,
    GL.GL_BOOL_VEC2: GL.glUniform2i,
    GL.GL_BOOL_VEC3: GL.glUniform3i,
    GL.GL_BOOL_VEC4: GL.glUniform4i,
    GL.GL_FLOAT_MAT2: GL.glUniformMatrix2fv,
    GL.GL_FLOAT_MAT3: GL.glUniformMatrix3fv,
    GL.GL_FLOAT_MAT4: GL.glUniformMatrix4fv,
    GL.GL_FLOAT_MAT2x3: GL.glUniformMatrix2x3fv,
    GL.GL_FLOAT_MAT2x4: GL.glUniformMatrix2x4fv,
    GL.GL_FLOAT_MAT3x2: GL.glUniformMatrix3x2fv,
    GL.GL_FLOAT_MAT3x4: GL.glUniformMatrix3x4fv,
    GL.GL_FLOAT_MAT4x2: GL.glUniformMatrix4x2fv,
    GL.GL_FLOAT_MAT4x3: GL.glUniformMatrix4x3fv,
    GL.GL_DOUBLE_MAT2: GL.glUniformMatrix2dv,
    GL.GL_DOUBLE_MAT3: GL.glUniformMatrix3dv,
    GL.GL_DOUBLE_MAT4: GL.glUniformMatrix4dv,
    GL.GL_DOUBLE_MAT2x3: GL.glUniformMatrix2x3dv,
    GL.GL_DOUBLE_MAT2x4: GL.glUniformMatrix2x4dv,
    GL.GL_DOUBLE_MAT3x2: GL.glUniformMatrix3x2dv,
    GL.GL_DOUBLE_MAT3x4: GL.glUniformMatrix3x4dv,
    GL.GL_DOUBLE_MAT4x2: GL.glUniformMatrix4x2dv,
    GL.GL_DOUBLE_MAT4x3: GL.glUniformMatrix4x3dv,
}


def get(directory):
    """ Get and compile all vertex and fragment shaders from the
    provided directory.

    Vertex shaders are expected to end with ".vert.glsl" and fragment
    shaders are expected to end with ".frag.glsl"

    Args:
        directory (str): the directory to retrieve shaders from

    Returns:
        Tuple[Dict[str, int], Dict[str, int]]: A tuple of
            (vertShaders, fragShaders) where the dictionaries are keyed
            by the shader's name and the values are the GL int of the
            compiled shader
    """
    frag_shaders = {}
    for frag_shader_path in glob.iglob(os.path.join(directory, '*.frag.glsl')):
        name = re.sub(r'\.frag\.glsl$', '', os.path.basename(frag_shader_path))
        with open(frag_shader_path, 'r') as handle:
            contents = handle.read()
        try:
            frag_shaders[name] = GL.shaders.compileShader(contents, GL.GL_FRAGMENT_SHADER)
        except RuntimeError:
            print('error compiling fragment shader: {}'.format(frag_shader_path))
            raise

    vert_shaders = {}
    for vert_shader_path in glob.iglob(os.path.join(directory, '*.vert.glsl')):
        name = re.sub(r'\.vert\.glsl$', '', os.path.basename(vert_shader_path))
        with open(vert_shader_path, 'r') as handle:
            contents = handle.read()
        try:
            vert_shaders[name] = GL.shaders.compileShader(contents, GL.GL_VERTEX_SHADER)
        except RuntimeError:
            print('error compiling vertex shader: {}'.format(vert_shader_path))
            raise
    return vert_shaders, frag_shaders


def init():
    global CONSTANT, POINT, SURFACE, TEXT_3D
    vert_shaders, frag_shaders = get(os.path.dirname(__file__))
    CONSTANT = ShaderProgram(
        name='constant',
        shaders=[vert_shaders['constant'], frag_shaders['simple']]
    )
    POINT = ShaderProgram(
        name='point',
        shaders=[vert_shaders['point'], frag_shaders['simple']]
    )
    SURFACE = ShaderProgram(
        name='surface',
        shaders=[vert_shaders['surface'], frag_shaders['simple']]
    )
    TEXT_3D = ShaderProgram(
        name='text3d',
        shaders=[vert_shaders['text3d'], frag_shaders['text']]
    )
    for shader in frag_shaders.values() + vert_shaders.values():
        GL.glDeleteShader(shader)


class ShaderUniform(object):
    def __init__(self, name, size, type, location):
        # type: (str, int, int, int) -> None
        self.name = name
        self.size = size
        self.type = type
        self.location = location


class ShaderProgram(GL.shaders.ShaderProgram):
    """Subclass of OpenGl.GL.shaders.ShaderProgram to extend its functionality
    """

    def __new__(cls, name, shaders, **kwargs):
        """ Copy of the `compileProgram` function from OpenGL/GL/shaders.py
        but removes the glDeleteShader calls so shaders can be linked multiple
        times

        Args:
            name (str): the unique name of this shader program
            shaders (List[int]): arbitrary number of shaders to attach to the generated program.
            separable (bool): set the separable flag to allow for partial
                installation of shader into the pipeline (see glUseProgramStages)
            retrievable (bool): set the retrievable flag to allow retrieval of
                the program binary representation, (see glProgramBinary, glGetProgramBinary)

        Raises:
            RuntimeError: when a link/validation failure occurs
        """
        if name in REGISTRY:
            raise RuntimeError('There is already a shader named {!r}'.format(name))
        self = GL.shaders.ShaderProgram.__new__(cls, GL.glCreateProgram())
        self.name = name
        REGISTRY[name] = self

        # link the shaders in the program
        if kwargs.get('separable'):
            GL.glProgramParameteri(self, separate_shader_objects.GL_PROGRAM_SEPARABLE, GL.GL_TRUE)
        if kwargs.get('retrievable'):
            GL.glProgramParameteri(self, get_program_binary.GL_PROGRAM_BINARY_RETRIEVABLE_HINT, GL.GL_TRUE)
        for shader in shaders:
            GL.glAttachShader(self, shader)
        GL.glLinkProgram(self)

        # validate everything is setup correctly
        # NOTE: we need to bind a VAO before validating the shader.
        #       See the following for more information about why this is necessary
        #   https://stackoverflow.com/questions/39761456/why-does-glvalidateprogram-fail-when-no-vao-is-bound
        global _TMP_VAO
        if _TMP_VAO is None:
            _TMP_VAO = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(_TMP_VAO)

        self.check_linked()
        self.check_validate()

        # store all uniforms for the program
        self.uniforms = {}  # type: Dict[str, ShaderUniform]
        num_active_uniforms = GL.glGetProgramiv(self, GL.GL_ACTIVE_UNIFORMS)
        for i in range(num_active_uniforms):
            name, size, type = GL.glGetActiveUniform(self, i)
            location = GL.glGetUniformLocation(self, name)
            self.uniforms[name] = ShaderUniform(name, size, type, location)

        return self

    # def __init__(self, value, *args, **kwargs):
    #     super(ShaderProgram, self).__init__()

    def set_uniform(self, name, *args):
        uniform = self.uniforms[name]

        setter = _UNIFORM_TYPE_TO_SETTER.get(uniform.type, None)
        if not setter:
            raise NotImplementedError

        current_program = GL.glGetIntegerv(GL.GL_CURRENT_PROGRAM)
        if current_program != self:
            raise Exception('must bind the ShaderProgram before setting uniforms for it')

        setter(uniform.location, *args)

    def __enter__(self):
        super(ShaderProgram, self).__enter__()
        return self
