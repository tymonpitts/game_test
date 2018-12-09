import math

from OpenGL import GL


VERTICES = [
    #
    #        7      4
    #                     ^
    #   3      0          y
    #                    z x >
    #        6      5   L
    #
    #   2      1
    #
     0.5,  0.5,  0.5,
     0.5, -0.5,  0.5,
    -0.5, -0.5,  0.5,
    -0.5,  0.5,  0.5,
     0.5,  0.5, -0.5,
     0.5, -0.5, -0.5,
    -0.5, -0.5, -0.5,
    -0.5,  0.5, -0.5,
]

# normalized side for 45 degree normal
normalized_45 = math.sqrt(pow(0.5, 2) * 3)

NORMALS = [
     normalized_45,  normalized_45,  normalized_45,
     normalized_45, -normalized_45,  normalized_45,
    -normalized_45, -normalized_45,  normalized_45,
    -normalized_45,  normalized_45,  normalized_45,
     normalized_45,  normalized_45, -normalized_45,
     normalized_45, -normalized_45, -normalized_45,
    -normalized_45, -normalized_45, -normalized_45,
    -normalized_45,  normalized_45, -normalized_45,
]
DRAW_METHOD = GL.GL_TRIANGLES
INDICES = [
    # FRONT FACE
    0, 1, 2,
    2, 3, 0,

    # TOP FACE
    0, 3, 7,
    7, 4, 0,

    # RIGHT FACE
    0, 5, 1,
    0, 4, 5,

    # BACK FACE
    4, 6, 5,
    4, 7, 6,

    # BOTTOM FACE
    1, 5, 6,
    1, 6, 2,

    # LEFT FACE
    2, 6, 3,
    3, 6, 7,
]
