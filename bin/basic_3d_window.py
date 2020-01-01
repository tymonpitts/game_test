#! /usr/bin/python
import glfw
from OpenGL import GL

import game_core


class Window(game_core.AbstractWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.title = 'Basic 3D Window'
        self.camera = None  # type: game_core.AbstractCamera

    def init(self):
        super(Window, self).init()

        # hide the cursor and lock it to this window. GLFW will then take care
        # of all the details of cursor re-centering and offset calculation and
        # providing the application with a virtual cursor position
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        # create a camera
        self.camera = game_core.AbstractCamera(position=[1.0, 1.0, 2.5])
        self.camera.init(*glfw.get_framebuffer_size(self.window))

        # populate the constant shader's matrices
        with game_core.shaders.CONSTANT as shader:
            shader.set_uniform(
                'camera_to_clip_matrix',
                1,
                GL.GL_FALSE,
                self.camera.projection_matrix.tolist(),
            )

            inverse_camera_matrix = self.camera.matrix.inverse()
            shader.set_uniform(
                'world_to_camera_matrix',
                1,
                GL.GL_FALSE,
                inverse_camera_matrix.tolist()
            )

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        game_core.draw_coordinate_system(game_core.Matrix())


if __name__ == '__main__':
    Window().run()
