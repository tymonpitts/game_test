__all__ = ['draw_coordinate_system', 'Font']


import freetype
from OpenGL import GL
from typing import Dict, List, Tuple, TYPE_CHECKING

from . import FLOAT_SIZE
from . import shaders

if TYPE_CHECKING:
    from . import Matrix
    from . import Point


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


class Font(object):
    def __init__(self, path='/System/Library/Fonts/Courier.dfont', size=16):
        """
        Args:
            path (str): path to the font file
            size (int): point size of the font
        """
        self._face = freetype.Face(path)
        self._face.set_char_size(size * 64)  # char sizes are in 1/64th point size so mult by 64
        GL.glPixelStorei(GL.GL_UNPACK_ALIGNMENT, 1)  # Disable byte-alignment restriction
        self._characters = {}  # type: Dict[str, _FontCharacter]
        for char_num in range(255):
            # Load character glyph and generate OpenGL texture
            char = chr(char_num)
            self._face.load_char(char)
            bitmap = self._face.glyph.bitmap
            texture = GL.glGenTextures(1)
            GL.glBindTexture(GL.GL_TEXTURE_2D, texture)
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,  # target
                0,  # level
                GL.GL_RED,  # internalformat
                bitmap.width,  # width
                bitmap.rows,  # height
                0,  # border
                GL.GL_RED,  # format
                GL.GL_UNSIGNED_BYTE,  # type
                bitmap.buffer  # pixels
            )
            # Set texture options and store the character for later use
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_S, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_WRAP_T, GL.GL_CLAMP_TO_EDGE)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_LINEAR)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_LINEAR)
            self._characters[char] = _FontCharacter(
                texture,
                (bitmap.width, bitmap.rows),
                (self._face.glyph.bitmap_left, self._face.glyph.bitmap_top),
                self._face.glyph.advance.x,
            )
        GL.glEnable(GL.GL_BLEND)
        GL.glBlendFunc(GL.GL_SRC_ALPHA, GL.GL_ONE_MINUS_SRC_ALPHA)

        # initialize VAO and VBO for rendering text.
        # The 2D quad requires 6 vertices (2 triangles) of 4 floats each
        # (2 for clip space vertex position and 2 for uv coordinates) so we
        # reserve 6 * 4 floats of memory. Because we'll be updating the
        # content of the VBO's memory quite often we'll allocate the memory
        # with GL_DYNAMIC_DRAW.
        self._vertex_array = GL.glGenVertexArrays(1)
        self._vertex_buffer = GL.glGenBuffers(1)
        GL.glBindVertexArray(self._vertex_array)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertex_buffer)
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            FLOAT_SIZE * 6 * 4,
            None,
            GL.GL_DYNAMIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(0, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glVertexAttribPointer(1, 2, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(6 * 2 * FLOAT_SIZE))
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)

    def render_3d(self, window_size, text, pos, scale=1.0, color=(1.0, 0.0, 0.0, 1.0)):
        # type: (Tuple[float, float], str, Point, float, Tuple[float, float, float, float]) -> None
        """ Render the provided text at a point in 3D space using this font

        Args:
            window_size (Tuple[float, float]): the (width, height) of the
                window we're rendering into. This helps compute where to draw
                the text
            text (str): text to render
            pos (Point): lower left corner of the text in 3D space
            scale (float): scale factor for this font's size
            color (Tuple[float, float, float, float]): color of the text
        """
        screen_space_offset_x = 5
        screen_space_offset_y = 5
        with shaders.TEXT_3D as shader:
            shader.set_uniform('color', *color)
            shader.set_uniform('world_position', *pos[:3])
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindVertexArray(self._vertex_array)

            for char in text:
                text_char = self._characters[char]

                screen_space_x = screen_space_offset_x + text_char.bearing[0] * scale
                screen_space_y = screen_space_offset_y - (text_char.size[1] - text_char.bearing[1]) * scale

                w = text_char.size[0] * scale
                h = text_char.size[1] * scale
                # Update VBO for each character
                screen_space_vertexes = [
                    [screen_space_x,     screen_space_y + h],
                    [screen_space_x + w, screen_space_y],
                    [screen_space_x,     screen_space_y],
                    [screen_space_x,     screen_space_y + h],
                    [screen_space_x + w, screen_space_y + h],
                    [screen_space_x + w, screen_space_y],
                ]
                clip_space_vertexes_flat = [
                    screen_space_vertex[i] / window_size[i] * 2
                    for screen_space_vertex in screen_space_vertexes
                    for i in range(2)
                ]
                uvs = [
                    0.0, 0.0,
                    1.0, 1.0,
                    0.0, 1.0,
                    0.0, 0.0,
                    1.0, 0.0,
                    1.0, 1.0,
                ]

                # Render glyph texture over quad
                GL.glBindTexture(GL.GL_TEXTURE_2D, text_char.texture)
                # Update content of VBO memory
                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self._vertex_buffer)
                data = clip_space_vertexes_flat + uvs
                array_type = (GL.GLfloat * len(data))
                GL.glBufferSubData(GL.GL_ARRAY_BUFFER, 0, FLOAT_SIZE * len(data), array_type(*data))
                GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
                # Render quad
                GL.glDrawArrays(GL.GL_TRIANGLES, 0, 6)
                # Now advance cursors for next glyph (note that advance is number of 1/64 pixels)
                screen_space_offset_x += (text_char.advance >> 6) * scale  # Bitshift by 6 to get value in pixels (2^6 = 64)
            GL.glBindVertexArray(0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, 0)


class _FontCharacter(object):
    """ Helper struct for the Font class to store information relating to a
    single character
    """
    def __init__(self, texture, size, bearing, advance):
        # type: (int, Tuple[int, int], Tuple[int, int], int) -> None
        """
        Args:
            texture (int): OpenGL ID handle of the glyph texture
            size (Tuple[int, int]): Size of glyph
            bearing (Tuple[int, int]: Offset from baseline to left/top of glyph
            advance (int): Offset to advance to next glyph
        """
        self.texture = texture
        self.size = size
        self.bearing = bearing
        self.advance = advance
