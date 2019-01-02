import math

from OpenGL import GL


VERTICES = (
    # Vert indexes which match those of an Octree's child indexes
    #        2      3
    #                     ^
    #   6      7          y
    #                    z x >
    #        0      1   L
    #   
    #   4      5
    -0.5, -0.5, -0.5,
     0.5, -0.5, -0.5,
    -0.5,  0.5, -0.5,
     0.5,  0.5, -0.5,
    -0.5, -0.5,  0.5,
     0.5, -0.5,  0.5,
    -0.5,  0.5,  0.5,
     0.5,  0.5,  0.5,
)

# normalized side for 45 degree normal
normalized_45 = math.sqrt(pow(0.5, 2) * 3)

NORMALS = (
    -normalized_45, -normalized_45, -normalized_45,
     normalized_45, -normalized_45, -normalized_45,
    -normalized_45,  normalized_45, -normalized_45,
     normalized_45,  normalized_45, -normalized_45,
    -normalized_45, -normalized_45,  normalized_45,
     normalized_45, -normalized_45,  normalized_45,
    -normalized_45,  normalized_45,  normalized_45,
     normalized_45,  normalized_45,  normalized_45,
)
DRAW_METHOD = GL.GL_TRIANGLES
INDICES = (
    # FRONT FACE
    4, 6, 5,
    6, 7, 5,

    # TOP FACE
    2, 3, 7,
    7, 6, 2,

    # RIGHT FACE
    1, 5, 7,
    7, 3, 1,

    # BACK FACE
    0, 1, 2,
    2, 1, 3,

    # BOTTOM FACE
    0, 5, 1,
    0, 4, 5,

    # LEFT FACE
    0, 6, 4,
    0, 2, 6,
)
