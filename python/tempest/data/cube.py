from OpenGL import GL

VERTICES = [
        0.5, 0.5, 0.5, # FRONT
        0.5, -0.5, 0.5, 
        -0.5, -0.5, 0.5, 
        -0.5, 0.5, 0.5, 

        0.5, 0.5, 0.5, # TOP
        -0.5, 0.5, 0.5, 
        -0.5, 0.5, -0.5, 
        0.5, 0.5, -0.5, 

        0.5, 0.5, 0.5, # RIGHT
        0.5, 0.5, -0.5, 
        0.5, -0.5, -0.5, 
        0.5, -0.5, 0.5, 

        0.5, 0.5, -0.5, # BACK
        -0.5, 0.5, -0.5, 
        -0.5, -0.5, -0.5, 
        0.5, -0.5, -0.5, 

        0.5, -0.5, 0.5, # BOTTOM
        0.5, -0.5, -0.5, 
        -0.5, -0.5, -0.5, 
        -0.5, -0.5, 0.5, 

        -0.5, 0.5, 0.5, # LEFT
        -0.5, -0.5, 0.5, 
        -0.5, -0.5, -0.5, 
        -0.5, 0.5, -0.5, 
        ]
NORMALS = [
        0.0, 0.0, 1.0, # FRONT
        0.0, 0.0, 1.0, 
        0.0, 0.0, 1.0, 
        0.0, 0.0, 1.0, 

        0.0, 1.0, 0.0, # TOP
        0.0, 1.0, 0.0, 
        0.0, 1.0, 0.0, 
        0.0, 1.0, 0.0, 

        1.0, 0.0, 0.0, # RIGHT
        1.0, 0.0, 0.0,
        1.0, 0.0, 0.0,
        1.0, 0.0, 0.0,

        0.0, 0.0, -1.0, # BACK
        0.0, 0.0, -1.0, 
        0.0, 0.0, -1.0, 
        0.0, 0.0, -1.0, 

        0.0, -1.0, 0.0, # BOTTOM
        0.0, -1.0, 0.0, 
        0.0, -1.0, 0.0, 
        0.0, -1.0, 0.0, 

        -1.0, 0.0, 0.0, # LEFT
        -1.0, 0.0, 0.0, 
        -1.0, 0.0, 0.0, 
        -1.0, 0.0, 0.0, 
        ]
DRAW_METHOD = GL.GL_TRIANGLES
INDICES = [
        0, 1, 2, 
        2, 3, 0, 
        4, 5, 6, 
        6, 7, 4, 
        8, 9, 10, 
        10, 11, 8, 
        12, 13, 14, 
        14, 15, 12, 
        16, 17, 18, 
        18, 19, 16, 
        20, 21, 22, 
        22, 23, 20, 
        ]
