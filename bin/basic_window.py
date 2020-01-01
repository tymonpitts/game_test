#! /usr/bin/python
from OpenGL import GL
from OpenGL.GL.shaders import compileShader

import game_core


vert_shader_source = '''
#version 330

layout(location = 0) in vec3 position;

void main()
{
    gl_Position.xyz = position;
    gl_Position.w = 1.0;
}
'''

frag_shader_source = '''
#version 330

out vec3 color;

void main(){
    color = vec3(1,0,0);
}
'''


class BasicWindow(game_core.AbstractWindow):
    def __init__(self):
        super(BasicWindow, self).__init__()
        self.title = 'Basic Window'
        self.shader = None  # type: game_core.ShaderProgram
        self.ndc_vao = None  # type: int

    def init(self):
        super(BasicWindow, self).init()
        vert_shader = compileShader(vert_shader_source, GL.GL_VERTEX_SHADER)
        frag_shader = compileShader(frag_shader_source, GL.GL_FRAGMENT_SHADER)
        self.shader = game_core.shaders.ShaderProgram(vert_shader, frag_shader)

        self.ndc_vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.ndc_vao)

        vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        data = [
            -1.0, -1.0, 0.0,
            0.0, 1.0, 0.0,
            1.0, -1.0, 0.0,
        ]

        array_type = (GL.GLfloat*len(data))
        GL.glBufferData(
                GL.GL_ARRAY_BUFFER,
                len(data)*game_core.FLOAT_SIZE,
                array_type(*data),
                GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glBindVertexArray(0)

    def keyboard_event(self, key, scancode, action, mods):
        """
        Args:
            key (int): The keyboard key that was pressed or released.
            scancode (int): The system-specific scancode of the key.
            action (int): glfw.PRESS, glfw.RELEASE or glfw.REPEAT.
            mods (int): Bit field describing which modifier keys were held down.
        """
        print 'key pressed: key={}  scancode={}  action={}  mods={}'.format(key, scancode, action, mods)
        super(BasicWindow, self).keyboard_event(key, scancode, action, mods)

    def mouse_button_event(self, button, action, mods):
        """Called when a mouse button is pressed or released

        :param int button: The pressed/released mouse button
        :param int action: glfw.PRESS or glfw.RELEASE
        :param int mods: Bit field describing which modifier keys were held down.
        """
        print 'button pressed: button={}  action={}  mods={}'.format(button, action, mods)

    def reshape(self, w, h):
        print 'reshaping: w={} h={}'.format(w, h)
        super(BasicWindow, self).reshape(w, h)

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        with self.shader:
            GL.glBindVertexArray(self.ndc_vao)
            GL.glDrawArrays(GL.GL_TRIANGLES, 0, 3)
            GL.glBindVertexArray(0)


if __name__ == '__main__':
    BasicWindow().run()

