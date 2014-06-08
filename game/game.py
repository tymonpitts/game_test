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
        # self.camera = Camera((0.0, 0.0, 0.0))
        self.mouse_movement = (0.0,0.0)
        size = 16
        self.world = World(size)
        self.camera = Camera((0.0, size+size/8, -size*2))

        self.pressed_keys = set()
        self.cube = None
        self.shaders = {}

    def get_window_title(self):
        return 'Game Test'

    def get_window_size(self):
        return (500, 500)

    def init(self):
        self.cube = core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, data.cube.DRAW_METHOD)

        self.shaders['cube'] = core.BaseShader(VERTEX_SHADER, FRAGMENT_SHADER)
        self.shaders['cube'].store_uniform_location('modelToWorldMatrix')
        self.shaders['cube'].store_uniform_location('worldToCameraMatrix')
        self.shaders['cube'].store_uniform_location('cameraToClipMatrix')
        self.shaders['cube'].store_uniform_location('lightIntensity')
        self.shaders['cube'].store_uniform_location('diffuseColor')
        with self.shaders['cube'] as shader:
            GL.glUniform4f(shader.uniforms['lightIntensity'], 1.0, 1.0, 1.0, 1.0)

        self.world.generate_terrain()

        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)
        GL.glFrontFace(GL.GL_CW)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glDepthRange(0.0, 1.0)
        GL.glEnable(depth_clamp.GL_DEPTH_CLAMP)

        glfw.Disable(glfw.MOUSE_CURSOR)

    def retrieve_mouse_data(self):
        window_size = glfw.GetWindowSize()
        window_center = [window_size[0] / 2, window_size[1] / 2]

        mouse_pos = [float(p - window_center[i]) / window_center[i] for i,p in enumerate(glfw.GetMousePos())]
        self.mouse_movement = (mouse_pos[0], mouse_pos[1])

        glfw.SetMousePos(*window_center)

    def handle_input(self):
        self.camera.handle_input(self.pressed_keys, self.mouse_movement)

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
        with self.shaders['cube'] as shader:
            GL.glUniformMatrix4fv(shader.uniforms['worldToCameraMatrix'], 1, GL.GL_FALSE, self.camera.matrix.inverse().tolist())

            # GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)
            # model_mat = core.MatrixStack()
            # model_mat.scale([scale, scale, scale])
            # GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            # self.cube.render()

            # GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
            # model_mat = core.MatrixStack()
            # model_mat.translate([trans, 0.0, 0.0])
            # model_mat.scale([scale, scale, scale])
            # GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            # self.cube.render()

            # GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 1.0, 0.0, 1.0)
            # model_mat = core.MatrixStack()
            # model_mat.translate([0.0, trans, 0.0])
            # model_mat.scale([scale, scale, scale])
            # GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            # self.cube.render()

            # GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 0.0, 1.0, 1.0)
            # model_mat = core.MatrixStack()
            # model_mat.translate([0.0, 0.0, trans])
            # model_mat.scale([scale, scale, scale])
            # GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            # self.cube.render()

            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 1.0, 0.5, 1.0)
            self.world.render(self, shader)

        glfw.SwapBuffers()
        
    def reshape(self, w, h):
        self.camera.reshape(w, h)
        with self.shaders['cube'] as shader:
            GL.glUniformMatrix4fv(shader.uniforms['cameraToClipMatrix'], 1, GL.GL_FALSE, self.camera.projection_matrix.tolist())
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
                    print 'fps:',fps
                    # print 'mouse_movement:',str(self.mouse_movement)
                    # print 'camera_mat:'
                    # print self.camera.matrix
                    fps = 0
                fps += 1

                self.retrieve_mouse_data()
                self.handle_input()
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

VERTEX_SHADER = '''
#version 330

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

smooth out vec4 interpColor;

uniform vec4 lightIntensity;
uniform vec4 diffuseColor;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    vec4 position_in_world = modelToWorldMatrix * vec4(position, 1.0);
    gl_Position = cameraToClipMatrix * worldToCameraMatrix * position_in_world;

    vec4 normal_in_world = normalize(modelToWorldMatrix * vec4(normal, 0.0));
    vec4 cam_position = normalize(inverse(worldToCameraMatrix) * vec4(0.0, 0.0, 0.0, 1.0));

    float cosAngIncidence = dot(normal_in_world, cam_position);
    cosAngIncidence = clamp(cosAngIncidence, 0, 1);
    
    interpColor = lightIntensity * diffuseColor * cosAngIncidence;
}
'''.strip()

