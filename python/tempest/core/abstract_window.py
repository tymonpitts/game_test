#! /usr/bin/python
import time

import glfw
from OpenGL import GL
from OpenGL.GL.ARB import depth_clamp

class AbstractWindow(object):
    INSTANCE = None
    """:type: `AbstractWindow`"""

    def __init__(self):
        self.title = 'AbstractWindow'
        self.initial_width = 512
        self.initial_height = 512
        self.mouse_movement = (0.0, 0.0)
        self.pressed_keys = set()
        self.INSTANCE = self

    def init(self):
        glfw.Init()

        glfw.OpenWindowHint(glfw.OPENGL_VERSION_MAJOR, 3)
        glfw.OpenWindowHint(glfw.OPENGL_VERSION_MINOR, 2)
        glfw.OpenWindowHint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.OpenWindowHint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        glfw.OpenWindow(
            self.initial_width, self.initial_height,
            8, 8, 8,
            8, 24, 0,
            glfw.WINDOW
        )

        glfw.SetWindowTitle(self.title)
        glfw.SetWindowSizeCallback(self.reshape)
        glfw.SetKeyCallback(self.keyboard_event)
        glfw.SetMouseButtonCallback(self.mouse_button_event)

        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)
        GL.glFrontFace(GL.GL_CW)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glDepthRange(0.0, 1.0)
        GL.glEnable(depth_clamp.GL_DEPTH_CLAMP)

    def pre_integration(self):
        pass

    def integrate(self, t, delta_time):
        raise NotImplementedError

    def post_integration(self):
        pass

    def keyboard_event(self, key, press):
        if key == glfw.KEY_ESC:
            glfw.Terminate()
            return

        # TODO: possibly use glfwSetInputMode here instead
        if press:
            self.pressed_keys.add(key)
        else:
            self.pressed_keys.remove(key)

    def mouse_button_event(self, button, action):
        """Called when a mouse button is pressed or released

        :param int button: The pressed/released mouse button
        :param int action: GLFW_PRESS or GLFW_RELEASE
        """
        pass

    def clear(self):
        GL.glClearColor(0.5, 0.5, 0.5, 0.0)
        GL.glClearDepth(1.0)
        GL.glClear(GL.GL_COLOR_BUFFER_BIT | GL.GL_DEPTH_BUFFER_BIT)

    def draw(self):
        raise NotImplementedError

    def reshape(self, w, h):
        GL.glViewport(0, 0, w, h)

    def run(self):
        self.init()

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

                # integrate for every delta time
                # TODO: implement interpolator to fix temporal aliasing
                #
                self.pre_integration()
                accumulator += elapsed_time
                while accumulator >= delta_time:
                    self.integrate(t, delta_time)
                    t += delta_time
                    accumulator -= delta_time
                self.post_integration()

                # clear the screen and redraw
                #
                self.clear()
                self.draw()
                glfw.SwapBuffers()
            except:
                glfw.Terminate()
                raise
