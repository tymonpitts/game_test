import os
import sys
import time
import numpy
import math

import glfw
import OpenGL
from OpenGL import GL
from OpenGL import GLE
from OpenGL.GL.ARB import depth_clamp

from .. import core
from . import Camera

class Game(object):
    def __init__(self):
        self.elapsed_time = 0.0
        self.start_time = None
        self.camera = Camera()
        self.mouse_movement = core.Point(0,0)

        self.pressed_keys = set()
        self.cube = None
        self.shaders = {}

    def get_window_title(self):
        return 'Game Test'

    def get_window_size(self):
        return (500, 500)

    def init(self):
        self.cube = core.Mesh(VERTICES, INDICES, DRAW_METHOD)
        # self.cube = core.Mesh(VERTICES, NORMALS, INDICES, DRAW_METHOD)

        self.shaders['cube'] = core.BaseShader(VERTEX_SHADER, FRAGMENT_SHADER)
        self.shaders['cube'].store_uniform_location('modelToWorldMatrix')
        self.shaders['cube'].store_uniform_location('worldToCameraMatrix')
        self.shaders['cube'].store_uniform_location('cameraToClipMatrix')
        # self.shaders['cube'].store_uniform_location('dirToLight')
        # self.shaders['cube'].store_uniform_location('lightIntensity')
        self.shaders['cube'].store_uniform_location('diffuseColor')
        # with self.shaders['cube'] as shader:
        #     GL.glUniform4f(shader.uniforms['lightIntensity'], 1.0, 1.0, 1.0, 1.0)

        # GL.glEnable(GL.GL_CULL_FACE)
        # GL.glCullFace(GL.GL_BACK)
        # GL.glFrontFace(GL.GL_CW)

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
        self.mouse_movement = core.Point(mouse_pos[0], mouse_pos[1])

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
        GL.glClearColor(0.0, 0.0, 0.0, 0.0)
        GL.glClearDepth(1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

        with self.shaders['cube'] as shader:
            # dirToLight = core.Vector(-1.0, -1.0, -1.0).normal()
            # dirToLight *= self.camera.model_view_matrix
            # GL.glUniform4fv(shader.uniforms['dirToLight'], 1, dirToLight.tolist());


            scale = 1.0
            trans = 10.0

            GL.glUniformMatrix4fv(shader.uniforms['worldToCameraMatrix'], 1, GL.GL_FALSE, self.camera.model_view_matrix.tolist())

            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)
            model_mat = core.MatrixStack()
            model_mat.scale([scale, scale, scale])
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            self.cube.render()

            GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
            model_mat = core.MatrixStack()
            model_mat.translate([trans, 0.0, 0.0])
            model_mat.scale([scale, scale, scale])
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            self.cube.render()

            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 1.0, 0.0, 1.0)
            model_mat = core.MatrixStack()
            model_mat.translate([0.0, trans, 0.0])
            model_mat.scale([scale, scale, scale])
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            self.cube.render()

            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 0.0, 1.0, 1.0)
            model_mat = core.MatrixStack()
            model_mat.translate([0.0, 0.0, trans])
            model_mat.scale([scale, scale, scale])
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, model_mat.top().tolist())
            self.cube.render()

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
            cur_time = time.time()
            self.elapsed_time = cur_time - last_time
            last_time = cur_time

            if (cur_time - last_fps_time) >= 1.0:
                last_fps_time = cur_time
                print 'fps:',fps
                print 'mouse_movement:',str(self.mouse_movement)
                print 'camera_mat:'
                print str(self.camera.model_view_matrix)
                fps = 0
            fps += 1

            self.retrieve_mouse_data()
            self.handle_input()
            self.display()

# FRAGMENT_SHADER = '''
# #version 330

# smooth in vec4 interpColor;

# out vec4 outputColor;

# void main()
# {
#     outputColor = interpColor;
# }
# '''.strip()

# VERTEX_SHADER = '''
# #version 330

# layout(location = 0) in vec3 position;
# //layout(location = 1) in vec3 normal;

# smooth out vec4 interpColor;

# uniform vec4 dirToLight;
# uniform vec4 lightIntensity;
# uniform vec4 diffuseColor;

# uniform mat4 cameraToClipMatrix;
# uniform mat4 worldToCameraMatrix;
# uniform mat4 modelToCameraMatrix;

# void main()
# {
#     gl_Position = cameraToClipMatrix * (modelToCameraMatrix * vec4(position, 1.0));
    
#     //vec4 normCamSpace = normalize(modelToCameraMatrix * vec4(normal,0.0));
    
#     //float cosAngIncidence = dot(normCamSpace, dirToLight);
#     //cosAngIncidence = clamp(cosAngIncidence, 0, 1);
    
#     // interpColor = lightIntensity * diffuseColor * cosAngIncidence;
#     interpColor = diffuseColor;
# }
# '''.strip()


FRAGMENT_SHADER = '''
#version 330

uniform vec4 diffuseColor;

out vec4 outputColor;

void main()
{
    outputColor = diffuseColor;
}
'''.strip()

VERTEX_SHADER = '''
#version 330

layout(location = 0) in vec4 position;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    vec4 temp = modelToWorldMatrix * position;
    temp = worldToCameraMatrix * temp;
    gl_Position = cameraToClipMatrix * temp;
}
'''.strip()

VERTICES = [
        0.5, 0.5, 0.5, # FRONT
        0.5, -0.5, 0.5, 
        -0.5, -0.5, 0.5, 
        -0.5, 0.5, 0.5, 

        0.5, 0.5, 0.5, # TOP
        -0.5, 0.5, 0.5, 
        -0.5, 0.5, -0.5, 
        0.5, 0.5, -0.5, 

        0.5, 0.5, 0.5, # RIGHT
        0.5, 0.5, -0.5, 
        0.5, -0.5, -0.5, 
        0.5, -0.5, 0.5, 

        0.5, 0.5, -0.5, # BACK
        -0.5, 0.5, -0.5, 
        -0.5, -0.5, -0.5, 
        0.5, -0.5, -0.5, 

        0.5, -0.5, 0.5, # BOTTOM
        0.5, -0.5, -0.5, 
        -0.5, -0.5, -0.5, 
        -0.5, -0.5, 0.5, 

        -0.5, 0.5, 0.5, # LEFT
        -0.5, -0.5, 0.5, 
        -0.5, -0.5, -0.5, 
        -0.5, 0.5, -0.5, 
        ]
NORMALS = [
        0.0, 0.0, 1.0, # FRONT
        0.0, 0.0, 1.0, 
        0.0, 0.0, 1.0, 
        0.0, 0.0, 1.0, 

        0.0, 1.0, 0.0, # TOP
        0.0, 1.0, 0.0, 
        0.0, 1.0, 0.0, 
        0.0, 1.0, 0.0, 

        1.0, 0.0, 0.0, # RIGHT
        1.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 0.0, 0.0,

        0.0, 0.0, -1.0, # BACK
        0.0, 0.0, -1.0, 
        0.0, 0.0, -1.0, 
        0.0, 0.0, -1.0, 

        0.0, -1.0, 0.0, # BOTTOM
        0.0, -1.0, 0.0, 
        0.0, -1.0, 0.0, 
        0.0, -1.0, 0.0, 

        -1.0, 0.0, 0.0, # LEFT
        -1.0, 0.0, 0.0, 
        -1.0, 0.0, 0.0, 
        -1.0, 0.0, 0.0, 
        ]
DRAW_METHOD = GL.GL_TRIANGLES
INDICES = [
        0, 1, 2, 
        2, 3, 0, 
        4, 5, 6, 
        6, 7, 4, 
        8, 9, 10, 
        10, 11, 8, 
        12, 13, 14, 
        14, 15, 12, 
        16, 17, 18, 
        18, 19, 16, 
        20, 21, 22, 
        22, 23, 20, 
        ]

