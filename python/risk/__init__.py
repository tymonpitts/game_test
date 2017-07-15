import glfw
from OpenGL import GL

import game_core
from . import data
from . import shaders

class Risk(game_core.AbstractWindow):
    INSTANCE = None  # type: Risk

    def __init__(self):
        super(Risk, self).__init__()
        self.title = 'Risk'
        self.shaders = None  # type: dict[str, game_core.ShaderProgram]

    def init(self):
        super(Risk, self).init()
        glfw.Disable(glfw.MOUSE_CURSOR)

        self.shaders = shaders.init()

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        pass

    def reshape(self, w, h):
        super(Risk, self).reshape(w, h)


def main():
    Risk.run()
