from OpenGL import GL
from typing import Tuple

from . import FLOAT_SIZE

# import freetype
#
# face = freetype.Face('Vera.ttf')
# face.set_char_size(48 * 64)
# face.load_char('S')
# bitmap = face.glyph.bitmap
# print bitmap.buffer


class TextCharacter(object):
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


class Text(object):
    def __init__(self, text):
        self.text = text
        self.vao = None
        self.vbo = None

    def init(self):
        GL.glGenVertexArrays(1, self.vao)
        GL.glGenBuffers(1, self.vbo)
        GL.glBindVertexArray(self.vao)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, self.vbo)

        # The 2D quad requires 6 vertices of 4 floats each so we reserve 6 * 4
        # floats of memory. Because we'll be updating the content of the VBO's
        # memory quite often we'll allocate the memory with GL_DYNAMIC_DRAW.
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            FLOAT_SIZE * 6 * 4,
            None,
            GL.GL_DYNAMIC_DRAW
        )

        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 4, GL.GL_FLOAT, GL.GL_FALSE, 4 * FLOAT_SIZE, None)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, 0)
        GL.glBindVertexArray(0)
