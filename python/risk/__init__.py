import glfw

import game_core


class Risk(game_core.AbstractWindow):
    INSTANCE = None  # type: Risk

    def __init__(self):
        super(Risk, self).__init__()
        self.title = 'Risk'

    def init(self):
        super(Risk, self).init()
        glfw.set_input_mode(self.window, glfw.CURSOR, False)

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        pass

    def reshape(self, w, h):
        super(Risk, self).reshape(w, h)


def main():
    Risk.run()
