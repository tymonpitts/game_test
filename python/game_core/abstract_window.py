#! /usr/bin/python
import time
from typing import Tuple, TYPE_CHECKING

import glfw
from OpenGL import GL
from OpenGL.GL.ARB import depth_clamp

from . import shaders
from . import drawing

if TYPE_CHECKING:
    from . import Point
    from . import drawing


class AbstractWindow(object):
    INSTANCE = None  # type: AbstractWindow

    def __init__(self):
        self.title = 'AbstractWindow'
        self.window = None  # type: int
        self.initial_width = 512
        self.initial_height = 512
        self.mouse_movement = (0.0, 0.0)
        self.pressed_keys = set()
        self.new_pressed_keys = set()
        self.INSTANCE = self
        self.font = None  # type: drawing.Font

    def init(self):
        if not glfw.init():
            raise Exception('glfw failed to initialize')

        glfw.window_hint(glfw.CONTEXT_VERSION_MAJOR, 4)
        glfw.window_hint(glfw.CONTEXT_VERSION_MINOR, 1)
        glfw.window_hint(glfw.OPENGL_FORWARD_COMPAT, GL.GL_TRUE)
        glfw.window_hint(glfw.OPENGL_PROFILE, glfw.OPENGL_CORE_PROFILE)

        self.window = glfw.create_window(
            self.initial_width, self.initial_height,
            self.title, None, None
        )
        if not self.window:
            glfw.terminate()
            raise Exception('glfw failed to create a window')

        glfw.make_context_current(self.window)
        glfw.set_framebuffer_size_callback(self.window, self._reshape_callback)
        glfw.set_key_callback(self.window, self._key_callback)
        glfw.set_mouse_button_callback(self.window, self._mouse_button_callback)

        GL.glEnable(GL.GL_CULL_FACE)
        GL.glCullFace(GL.GL_BACK)
        GL.glFrontFace(GL.GL_CW)

        GL.glEnable(GL.GL_DEPTH_TEST)
        GL.glDepthMask(GL.GL_TRUE)
        GL.glDepthFunc(GL.GL_LEQUAL)
        GL.glDepthRange(0.0, 1.0)
        GL.glEnable(depth_clamp.GL_DEPTH_CLAMP)

        shaders.init()

        self.font = drawing.Font()

    def render_text_3d(self, text, pos, scale=1.0, color=(1.0, 0.0, 0.0, 1.0), font=None):
        # type: (str, Point, float, Tuple[float, float, float, float], drawing.Font) -> None
        """ Render the provided text at a point in 3D space

        Args:
            text (str): text to render
            pos (Point): lower left corner of the text in 3D space
            scale (float): scale factor for the font size
            color (Tuple[float, float, float, float]): color of the text
            font (drawing.Font): font to render the text with. If not provided
                then this defaults to the window's font
        """
        font = font or self.font
        window_size = glfw.get_framebuffer_size(self.window)
        font.render_3d(window_size, text, pos, scale, color)

    def pre_integration(self):
        pass

    def integrate(self, t, delta_time):
        raise NotImplementedError

    def post_integration(self):
        pass

    def _reshape_callback(self, window, w, h):
        # type: (glfw._GLFWwindow, int, int) -> None
        self.reshape(w, h)

    def _key_callback(self, window, key, scancode, action, mods):
        # type: (glfw._GLFWwindow, int, int, int, int) -> None
        self.keyboard_event(key, scancode, action, mods)

    def _mouse_button_callback(self, window, button, action, mods):
        # type: (glfw._GLFWwindow, int, int, int) -> None
        self.mouse_button_event(button, action, mods)

    def keyboard_event(self, key, scancode, action, mods):
        """
        Args:
            key (int): The keyboard key that was pressed or released.
            scancode (int): The system-specific scancode of the key.
            action (int): glfw.PRESS, glfw.RELEASE or glfw.REPEAT.
            mods (int): Bit field describing which modifier keys were held down.
        """
        if key == glfw.KEY_ESCAPE:
            print 'Escape pressed...'
            glfw.set_window_should_close(self.window, True)
            return

        # TODO: possibly use glfwSetInputMode here instead
        if action == glfw.PRESS:
            self.new_pressed_keys.add(key)  # removed later during the main loop
            self.pressed_keys.add(key)
        elif action == glfw.REPEAT:
            self.pressed_keys.add(key)
        else:
            self.pressed_keys.remove(key)

    def mouse_button_event(self, button, action, mods):
        """Called when a mouse button is pressed or released

        Args:
            button (int): The pressed/released mouse button
            action (int): glfw.PRESS or glfw.RELEASE
            mods (int): Bit field describing which modifier keys were held down.
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

    @classmethod
    def run(cls):
        self = cls()
        self.init()

        t = 0.0
        current_time = time.time()
        delta_time = 1.0 / 60.0
        accumulator = 0.0
        try:
            while not glfw.window_should_close(self.window):
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
                    self.new_pressed_keys.clear()
                self.post_integration()

                # clear the screen and redraw
                #
                self.clear()
                self.draw()
                glfw.swap_buffers(self.window)
                glfw.poll_events()
        except KeyboardInterrupt:
            print 'KeyboardInterrupt...'
        finally:
            print('Exiting...')
            glfw.terminate()
