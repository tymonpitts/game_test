import os
import time
import random

import glfw
from OpenGL import GL
from OpenGL.GL.ARB import depth_clamp

from .. import data
from .. import core


class Game(object):
    def __init__(self):
        self.mouse_movement = (0.0,0.0)

        self.pressed_keys = set()
        self.cube = None
        self.shaders = {}
        self.player = None
        self.world = None

        self.block_ids_to_cls = []

        self.do_printing = False

    def get_window_title(self):
        return 'Game Test'

    def get_window_size(self):
        return (500, 500)

    def init(self):
        self.cube = core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, data.cube.DRAW_METHOD)

        shaders_dir = os.path.dirname(__file__)
        shaders_dir = os.path.join(shaders_dir, '../shaders')
        shaders_dir = os.path.abspath(shaders_dir)

        frag_shader_path = os.path.join(shaders_dir, 'frag.frag.glsl')
        with open(frag_shader_path, 'r') as handle:
            frag_shader = handle.read()

        skin_shader_path = os.path.join(shaders_dir, 'skin.vert.glsl')
        with open(skin_shader_path, 'r') as handle:
            skin_shader = handle.read()

        constant_shader_path = os.path.join(shaders_dir, 'constant.vert.glsl')
        with open(constant_shader_path, 'r') as handle:
            constant_shader = handle.read()

        self.shaders['skin'] = core.BaseShader(skin_shader, frag_shader)
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

        self.shaders['constant'] = core.BaseShader(constant_shader, frag_shader)
        self.shaders['constant'].store_uniform_location('modelToWorldMatrix')
        self.shaders['constant'].store_uniform_location('worldToCameraMatrix')
        self.shaders['constant'].store_uniform_location('cameraToClipMatrix')
        self.shaders['constant'].store_uniform_location('color')

        self.register_blocks()

        from .world import World
        self.world = World(self, 128)

        # from .player import Player
        # x=0.5
        # z=-3.5
        # y = self.world.get_height(x,z)
        # self.player = Player(self, [x, y, z])

        from .spectator import Spectator
        x = 0.0
        z = 0.0
        y = 64.0
        self.player = Spectator([x, y, z])

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

    def get_block_cls(self, id):
        return self.block_ids_to_cls[id]

    def retrieve_mouse_data(self):
        window_size = glfw.GetWindowSize()
        window_center = [window_size[0] / 2, window_size[1] / 2]

        mouse_pos = [float(p - window_center[i]) / window_center[i] for i,p in enumerate(glfw.GetMousePos())]
        self.mouse_movement = (mouse_pos[0], mouse_pos[1])

        glfw.SetMousePos(*window_center)

    def integrate(self, t, delta_time):
        self.retrieve_mouse_data()
        self.player.update(t, delta_time)

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
            light_dir = core.Vector(0.1, 1.0, 0.5)
            light_dir.normalize()
            GL.glUniform4fv(shader.uniforms['dirToLight'], 1, list(light_dir))

        # # draw scene origin cubes
        # #
        # with self.shaders['skin'] as shader:
        #     mat = core.Matrix()
        #     mat.scale(0.1)
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)
        #     self.cube.render()
        #
        #     mat = core.Matrix()
        #     mat.scale(0.1)
        #     mat.translate([1,0,0])
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
        #     self.cube.render()
        #
        #     mat = core.Matrix()
        #     mat.scale(0.1)
        #     mat.translate([0,1,0])
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 1.0, 0.0, 1.0)
        #     self.cube.render()
        #
        #     mat = core.Matrix()
        #     mat.scale(0.1)
        #     mat.translate([0,0,1])
        #     GL.glUniformMatrix4fv(
        #             shader.uniforms['modelToWorldMatrix'],
        #             1,
        #             GL.GL_FALSE,
        #             mat.tolist())
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 0.0, 1.0, 1.0)
        #     self.cube.render()

        self.world.render()
        self.player.render()

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
        t = 0.0
        current_time = time.time()
        delta_time = 1.0 / 60.0
        accumulator = 0.0
        while glfw.GetWindowParam(glfw.OPENED):
            try:
                # get elapsed time
                #
                new_time = time.time()
                elapsed_time = new_time - current_time
                if elapsed_time > 0.25:
                    elapsed_time = 0.25
                current_time = new_time

                # compute for every delta time
                #
                accumulator += elapsed_time
                while accumulator >= delta_time:
                    self.integrate(t, delta_time)
                    t += delta_time
                    accumulator -= delta_time

                # TODO: implement interpolator to fix temporal aliasing

                # if (cur_time - last_fps_time) >= 1.0:
                #     last_fps_time = cur_time
                #     self.do_printing = True
                #     if fps < 60:
                #         print 'fps:',fps
                #     # print 'mouse_movement:',str(self.mouse_movement)
                #     # print 'camera_mat:'
                #     # print self.player.matrix
                #     fps = 0
                # else:
                #     self.do_printing = False
                # fps += 1

                self.display()
            except:
                glfw.Terminate()
                raise

