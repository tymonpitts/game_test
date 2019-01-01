import os
import glob
import re
import game_core
from OpenGL import GL
from OpenGL.GL.shaders import compileShader

def init():
    shaders_dir = os.path.abspath( os.path.dirname(__file__) )

    frag_shaders = {}
    for frag_shader_path in glob.iglob('%s/*.frag.glsl' % shaders_dir):
        name = re.sub( r'\.frag\.glsl$', '', os.path.basename(frag_shader_path) )
        with open(frag_shader_path, 'r') as handle:
            contents = handle.read()
        frag_shaders[name] = compileShader(contents, GL.GL_FRAGMENT_SHADER)

    vert_shaders = {}
    for vert_shader_path in glob.iglob('%s/*.vert.glsl' % shaders_dir):
        name = re.sub( r'\.vert\.glsl$', '', os.path.basename(vert_shader_path) )
        with open(vert_shader_path, 'r') as handle:
            contents = handle.read()
        vert_shaders[name] = compileShader(contents, GL.GL_VERTEX_SHADER)

    shaders = {}
    shaders['skin'] = game_core.ShaderProgram(vert_shaders['skin'], frag_shaders['frag'])
    shaders['skin'].store_uniform_location('modelToWorldMatrix')
    shaders['skin'].store_uniform_location('worldToCameraMatrix')
    shaders['skin'].store_uniform_location('cameraToClipMatrix')
    shaders['skin'].store_uniform_location('lightIntensity')
    shaders['skin'].store_uniform_location('ambientIntensity')
    shaders['skin'].store_uniform_location('diffuseColor')
    shaders['skin'].store_uniform_location('dirToLight')
    with shaders['skin'] as shader:
        GL.glUniform4f(shader.uniforms['lightIntensity'], 0.8, 0.8, 0.8, 1.0)
        GL.glUniform4f(shader.uniforms['ambientIntensity'], 0.2, 0.2, 0.2, 1.0)

    shaders['lod_test'] = game_core.ShaderProgram(vert_shaders['lod_test'], frag_shaders['frag'])
    shaders['lod_test'].store_uniform_location('transitionEndDistance')
    shaders['lod_test'].store_uniform_location('transitionRange')
    shaders['lod_test'].store_uniform_location('cameraWorldPosition')
    shaders['lod_test'].store_uniform_location('modelToWorldMatrix')
    shaders['lod_test'].store_uniform_location('worldToCameraMatrix')
    shaders['lod_test'].store_uniform_location('cameraToClipMatrix')
    shaders['lod_test'].store_uniform_location('lightIntensity')
    shaders['lod_test'].store_uniform_location('ambientIntensity')
    shaders['lod_test'].store_uniform_location('diffuseColor')
    shaders['lod_test'].store_uniform_location('dirToLight')
    with shaders['lod_test'] as shader:
        GL.glUniform4f(shader.uniforms['lightIntensity'], 0.8, 0.8, 0.8, 1.0)
        GL.glUniform4f(shader.uniforms['ambientIntensity'], 0.2, 0.2, 0.2, 1.0)

    shaders['ndc'] = game_core.ShaderProgram(vert_shaders['ndc'], frag_shaders['ndc'])

    shaders['simple'] = game_core.ShaderProgram(vert_shaders['simple'], frag_shaders['simple'])
    shaders['simple'].store_uniform_location('modelToWorldMatrix')
    shaders['simple'].store_uniform_location('worldToCameraMatrix')
    shaders['simple'].store_uniform_location('cameraToClipMatrix')

    shaders['point'] = game_core.ShaderProgram(vert_shaders['point'], frag_shaders['frag'])
    shaders['point'].store_uniform_location('modelToWorldMatrix')
    shaders['point'].store_uniform_location('worldToCameraMatrix')
    shaders['point'].store_uniform_location('cameraToClipMatrix')
    shaders['point'].store_uniform_location('color')

    shaders['constant'] = game_core.ShaderProgram(vert_shaders['constant'], frag_shaders['frag'])
    shaders['constant'].store_uniform_location('modelToWorldMatrix')
    shaders['constant'].store_uniform_location('worldToCameraMatrix')
    shaders['constant'].store_uniform_location('cameraToClipMatrix')
    shaders['constant'].store_uniform_location('color')

    shaders['heightmap'] = game_core.ShaderProgram(vert_shaders['heightmap'], frag_shaders['heightmap'])
    shaders['heightmap'].store_uniform_location('textureSampler')

    for shader in frag_shaders.values() + vert_shaders.values():
        GL.glDeleteShader(shader)

    return shaders
