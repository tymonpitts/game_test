__all__ = ['draw_coordinate_system']


from OpenGL import GL
from typing import List, TYPE_CHECKING

from . import FLOAT_SIZE
from . import shaders

if TYPE_CHECKING:
    from . import Matrix


def draw_coordinate_system(matrix):
    # type: (Matrix) -> None
    if not draw_coordinate_system.vaos:
        draw_coordinate_system.vaos = []
        for i in range(3):
            vao = GL.glGenVertexArrays(1)
            draw_coordinate_system.vaos.append(vao)
            vbo = GL.glGenBuffers(1)
            data = [0.0] * 6
            data[i] = 1.0
            array_type = (GL.GLfloat * len(data))
            GL.glBindVertexArray(vao)
            GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vbo)
            GL.glBufferData(GL.GL_ARRAY_BUFFER, FLOAT_SIZE * len(data), array_type(*data), GL.GL_STATIC_DRAW)
            GL.glEnableVertexAttribArray(0)
            GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

    with shaders.CONSTANT as shader:
        for i in range(3):
            color = [0.0, 0.0, 0.0, 1.0]
            color[i] = 1.0
            shader.set_uniform('color', *color)
            shader.set_uniform(
                'model_to_world_matrix',
                1,
                GL.GL_FALSE,
                matrix.tolist(),
            )
            GL.glBindVertexArray(draw_coordinate_system.vaos[i])
            GL.glDrawArrays(GL.GL_LINES, 0, 2)
    GL.glBindVertexArray(0)


draw_coordinate_system.vaos = None  # type: List[int]
