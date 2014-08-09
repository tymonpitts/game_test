import os
import sys
import time
import numpy
import math
import random

import glfw
import OpenGL
from OpenGL import GL
from OpenGL import GLE
from OpenGL.GL.ARB import depth_clamp

from .. import data
from .. import core
from . import Camera
from . import World

class Game(object):
    def __init__(self):
        self.elapsed_time = 0.0
        self.start_time = None
        self.mouse_movement = (0.0,0.0)

        self.pressed_keys = set()
        self.cube = None
        self.shaders = {}
        self.player = None
        self.world = None
        # self.collider = None

        self.block_ids_to_cls = []

        self.do_printing = False

    def get_window_title(self):
        return 'Game Test'

    def get_window_size(self):
        return (500, 500)

    def init(self):
        self.cube = core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, data.cube.DRAW_METHOD)

        self.shaders['skin'] = core.BaseShader(VERTEX_SHADER, FRAGMENT_SHADER)
        self.shaders['skin'].store_uniform_location('modelToWorldMatrix')
        self.shaders['skin'].store_uniform_location('worldToCameraMatrix')
        self.shaders['skin'].store_uniform_location('cameraToClipMatrix')
        self.shaders['skin'].store_uniform_location('lightIntensity')
        self.shaders['skin'].store_uniform_location('ambientIntensity')
        self.shaders['skin'].store_uniform_location('diffuseColor')
        self.shaders['skin'].store_uniform_location('dirToLight')
        with self.shaders['skin'] as shader:
            GL.glUniform4f(shader.uniforms['lightIntensity'], 0.8, 0.8, 0.8, 1.0)
            GL.glUniform4f(shader.uniforms['ambientIntensity'], 0.2, 0.2, 0.2, 1.0)

        self.shaders['constant'] = core.BaseShader(CONSTANT_SHADER, FRAGMENT_SHADER)
        self.shaders['constant'].store_uniform_location('modelToWorldMatrix')
        self.shaders['constant'].store_uniform_location('worldToCameraMatrix')
        self.shaders['constant'].store_uniform_location('cameraToClipMatrix')
        self.shaders['constant'].store_uniform_location('color')

        self.register_blocks()

        from .world import World
        self.world = World(128)

        from .player import Player
        x=0.5
        z=-3.5
        y = self.world.get_height(x,z)
        self.player = Player([x, y, z])

        # from ..tests import collision
        # self.player = collision.Camera()
        # self.collider = collision.Collider()
        # self.world = collision.World()

        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)
        GL.glFrontFace(GL.GL_CW)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glDepthRange(0.0, 1.0)
        GL.glEnable(depth_clamp.GL_DEPTH_CLAMP)

        glfw.Disable(glfw.MOUSE_CURSOR)

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

    def retrieve_mouse_data(self):
        window_size = glfw.GetWindowSize()
        window_center = [window_size[0] / 2, window_size[1] / 2]

        mouse_pos = [float(p - window_center[i]) / window_center[i] for i,p in enumerate(glfw.GetMousePos())]
        self.mouse_movement = (mouse_pos[0], mouse_pos[1])

        glfw.SetMousePos(*window_center)

    def update(self):
        self.player.update(self)
        # self.collider.update(self)

    def keyboard(self, key, press):
        if key == glfw.KEY_ESC:
            glfw.Terminate()
            return

        if press:
            self.pressed_keys.add(key)
        else:
            self.pressed_keys.remove(key)

    def display(self):
        GL.glClearColor(0.5, 0.5, 0.5, 0.0)
        GL.glClearDepth(1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        random.seed(1121327837)
        i_cam_mat = self.player.camera_matrix().inverse()
        for shader in self.shaders.itervalues():
            with shader:
                GL.glUniformMatrix4fv(shader.uniforms['worldToCameraMatrix'], 1, GL.GL_FALSE, i_cam_mat.tolist())

        with self.shaders['skin'] as shader:
            light_dir = core.Vector([0.1, 1.0, 0.5])
            light_dir.normalize()
            light_dir *= i_cam_mat
            GL.glUniform4fv(shader.uniforms['dirToLight'], 1, light_dir.tolist())

        self.world.render(self)
        self.player.render(self)

        # self.world.render(self)
        # self.collider.render(self)

        glfw.SwapBuffers()
        
    def reshape(self, w, h):
        self.player.reshape(w, h)
        for shader in self.shaders.itervalues():
            with shader:
                GL.glUniformMatrix4fv(
                        shader.uniforms['cameraToClipMatrix'], 
                        1, 
                        GL.GL_FALSE, 
                        self.player.projection_matrix.tolist())
        GL.glViewport(0, 0, w, h)

        window_center = [w / 2, h / 2]
        glfw.SetMousePos(*window_center)

    def run(self):
        glfw.Init()
         
        glfw.OpenWindowHint(glfw.OPENGL_VERSION_MAJOR, 3);
        glfw.OpenWindowHint(glfw.OPENGL_VERSION_MINOR, 2)
        glfw.OpenWindowHint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.OpenWindowHint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)
         
        width, height = self.get_window_size()
        glfw.OpenWindow(
            width, height,
            8, 8, 8,
            8, 24, 0,
            glfw.WINDOW
            )
        
        glfw.SetWindowTitle(self.get_window_title())

        self.init()

        glfw.SetWindowSizeCallback(self.reshape)
        glfw.SetKeyCallback(self.keyboard)

        fps = 0
        self.start_time = last_time = last_fps_time = time.time()
        while glfw.GetWindowParam(glfw.OPENED):
            try:
                cur_time = time.time()
                self.elapsed_time = cur_time - last_time
                last_time = cur_time

                if (cur_time - last_fps_time) >= 1.0:
                    last_fps_time = cur_time
                    self.do_printing = True
                    # print 'fps:',fps
                    # print 'mouse_movement:',str(self.mouse_movement)
                    # print 'camera_mat:'
                    # print self.player.matrix
                    fps = 0
                else:
                    self.do_printing = False
                fps += 1

                self.retrieve_mouse_data()
                self.update()
                self.display()
            except:
                glfw.Terminate()
                raise

FRAGMENT_SHADER = '''
#version 330

smooth in vec4 interpColor;

out vec4 outputColor;

void main()
{
    outputColor = interpColor;
}
'''.strip()

# # light from camera
# #
# VERTEX_SHADER = '''
# #version 330

# layout(location = 0) in vec3 position;
# layout(location = 1) in vec3 normal;

# smooth out vec4 interpColor;

# uniform vec4 lightIntensity;
# uniform vec4 diffuseColor;

# uniform mat4 cameraToClipMatrix;
# uniform mat4 worldToCameraMatrix;
# uniform mat4 modelToWorldMatrix;

# void main()
# {
#     vec4 position_in_world = modelToWorldMatrix * vec4(position, 1.0);
#     gl_Position = cameraToClipMatrix * worldToCameraMatrix * position_in_world;

#     vec4 normal_in_world = normalize(modelToWorldMatrix * vec4(normal, 0.0));
#     vec4 cam_position = normalize(inverse(worldToCameraMatrix) * vec4(0.0, 0.0, 0.0, 1.0));

#     float cosAngIncidence = dot(normal_in_world, cam_position);
#     cosAngIncidence = clamp(cosAngIncidence, 0, 1);
    
#     interpColor = lightIntensity * diffuseColor * cosAngIncidence;
# }
# '''.strip()

# directional light with ambient lighting
#
VERTEX_SHADER = '''
#version 330

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

smooth out vec4 interpColor;

uniform vec4 lightIntensity;
uniform vec4 ambientIntensity;
uniform vec4 diffuseColor;
uniform vec4 dirToLight;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    mat4 model_to_camera = worldToCameraMatrix * modelToWorldMatrix;
    gl_Position = cameraToClipMatrix * model_to_camera * vec4(position, 1.0);

    vec4 normal_in_world = normalize(model_to_camera * vec4(normal, 0.0));

    float cosAngIncidence = dot(normal_in_world, dirToLight);
    cosAngIncidence = clamp(cosAngIncidence, 0, 1);

    float mult = ((position[1])/20.0);
    interpColor = ((diffuseColor * lightIntensity * cosAngIncidence) +
        (diffuseColor * ambientIntensity)) * vec4(mult,mult,mult,1.0);

}
'''.strip()


# constant color
#
CONSTANT_SHADER = '''
#version 330

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

smooth out vec4 interpColor;

uniform vec4 color;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    mat4 model_to_camera = worldToCameraMatrix * modelToWorldMatrix;
    gl_Position = cameraToClipMatrix * model_to_camera * vec4(position, 1.0);
    interpColor = color;
}
'''.strip()

