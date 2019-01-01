#! /usr/bin/python
import glfw
from OpenGL import GL
from OpenGL.GL.shaders import compileShader

import game_core
from tempest.data.lod_transition_proof_of_concept import smooth_cube


frag_shader_source = '''
#version 330

smooth in vec3 interpColor;

out vec3 color;

void main(){
    color = interpColor;
}
'''


vert_shader_source = '''
#version 330

layout(location = 0) in vec3 position;
layout(location = 1) in vec3 normal;

smooth out vec3 interpColor;

uniform mat4 cameraToClipMatrix;
uniform mat4 worldToCameraMatrix;
uniform mat4 modelToWorldMatrix;

void main()
{
    gl_Position = cameraToClipMatrix * worldToCameraMatrix * modelToWorldMatrix * vec4(position, 1.0);
    interpColor = normal;
}
'''


class Window(game_core.AbstractWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.title = 'Basic 3D Window'
        self.cube = None  # type: game_core.Mesh
        self.shader = None  # type: game_core.ShaderProgram
        self.camera = None  # type: game_core.AbstractCamera

    def init(self):
        super(Window, self).init()

        # hide the cursor and lock it to this window. GLFW will then take care
        # of all the details of cursor re-centering and offset calculation and
        # providing the application with a virtual cursor position
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        # create a simple cube with smooth normals
        self.cube = game_core.Mesh(smooth_cube.VERTICES, smooth_cube.NORMALS, smooth_cube.INDICES, smooth_cube.DRAW_METHOD)

        # create a camera
        self.camera = game_core.AbstractCamera(position=[0.0, 0.0, 1.5])
        self.camera.init(*glfw.get_framebuffer_size(self.window))

        # compile a simple shader with MVP matrices
        frag_shader = compileShader(frag_shader_source, GL.GL_FRAGMENT_SHADER)
        vert_shader = compileShader(vert_shader_source, GL.GL_VERTEX_SHADER)
        self.shader = game_core.ShaderProgram(vert_shader, frag_shader)
        self.shader.store_uniform_location('modelToWorldMatrix')
        self.shader.store_uniform_location('worldToCameraMatrix')
        self.shader.store_uniform_location('cameraToClipMatrix')

        # populate the shader's MVP matrices and pull the "camera" back 1.5 units
        with self.shader:
            GL.glUniformMatrix4fv(
                self.shader.uniforms['cameraToClipMatrix'],
                1,
                GL.GL_FALSE,
                self.camera.projection_matrix.tolist(),
            )

            inverse_camera_matrix = self.camera.matrix.inverse()
            GL.glUniformMatrix4fv(
                self.shader.uniforms['worldToCameraMatrix'],
                1,
                GL.GL_FALSE,
                inverse_camera_matrix.tolist()
            )

            model_mat = game_core.Matrix()
            GL.glUniformMatrix4fv(
                self.shader.uniforms['modelToWorldMatrix'],
                1,
                GL.GL_FALSE,
                model_mat.tolist()
            )

    def integrate(self, t, delta_time):
        pass

    def draw(self):
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        with self.shader:
            self.cube.render()


if __name__ == '__main__':
    Window().run()
