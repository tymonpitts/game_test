#! /usr/bin/python
import math

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

    def build_perspective_matrix(self):
        # type: () -> game_core.Matrix
        """ Create a perspective matrix the same way GLU does

        Code transposed from gluPerspective
        """
        aspect = float(self.initial_width) / float(self.initial_height)
        near = 0.1
        far = 10.0
        fovy = 45.0
        ymax = near * math.tan(math.radians(fovy))
        xmax = ymax * aspect

        left = -xmax
        right = xmax
        bottom = -ymax
        top = ymax

        temp = 2.0 * near
        temp2 = right - left
        temp3 = top - bottom
        temp4 = far - near

        result = game_core.Matrix()
        result[0, 0] = temp / temp2
        result[1, 1] = temp / temp3

        result[2, 0] = (right + left) / temp2
        result[2, 1] = (top + bottom) / temp3
        result[2, 2] = (-far - near) / temp4
        result[2, 3] = -1.0

        result[3, 2] = (-temp * far) / temp4
        result[3, 3] = 0.0
        return result

    def init(self):
        super(Window, self).init()

        # hide the cursor and lock it to this window. GLFW will then take care
        # of all the details of cursor re-centering and offset calculation and
        # providing the application with a virtual cursor position
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        # create a simple cube with smooth normals
        self.cube = game_core.Mesh(smooth_cube.VERTICES, smooth_cube.NORMALS, smooth_cube.INDICES, smooth_cube.DRAW_METHOD)

        # compile a simple shader with MVP matrices
        frag_shader = compileShader(frag_shader_source, GL.GL_FRAGMENT_SHADER)
        vert_shader = compileShader(vert_shader_source, GL.GL_VERTEX_SHADER)
        self.shader = game_core.ShaderProgram(vert_shader, frag_shader)
        self.shader.store_uniform_location('modelToWorldMatrix')
        self.shader.store_uniform_location('worldToCameraMatrix')
        self.shader.store_uniform_location('cameraToClipMatrix')

        # populate the shader's MVP matrices and pull the "camera" back 1.5 units
        with self.shader:
            print('Setting cameraToClipMatrix:')
            perspective_matrix = self.build_perspective_matrix()
            print(perspective_matrix)
            GL.glUniformMatrix4fv(
                self.shader.uniforms['cameraToClipMatrix'],
                1,
                GL.GL_FALSE,
                perspective_matrix.tolist(),
            )
            print('Setting worldToCameraMatrix:')
            camera_matrix = game_core.Matrix()
            camera_matrix[3, 2] = 1.5
            inverse_camera_matrix = camera_matrix.inverse()
            print(inverse_camera_matrix)
            GL.glUniformMatrix4fv(
                self.shader.uniforms['worldToCameraMatrix'],
                1,
                GL.GL_FALSE,
                inverse_camera_matrix.tolist()
            )
            print('Setting modelToWorldMatrix:')
            model_mat = game_core.Matrix()
            print(model_mat)
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
