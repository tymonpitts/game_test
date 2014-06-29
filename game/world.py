#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import random
import time

import numpy
import glfw
import noise

from OpenGL import GL

from .. import core

from ..core.logger import *

#============================================================================#
#=============================================================== FUNCTIONS ==#
def clamp(v, min_, max_):
    return max(min(v, max_), min_)

def fractal_rand():
    return (random.random() * 2.0) - 1.0

def avg_vals(i, j, values):
    return (values[i-1][j-1] + 
            values[i-1][j] +
            values[i][j-1] +
            values[i][j]) * 0.25

def avg_square_vals(i, j, stride, values):
    return (values[i-stride][j-stride] + 
            values[i-stride][j+stride] +
            values[i+stride][j-stride] +
            values[i+stride][j+stride]) * 0.25

def avg_diamond_vals(i, j, stride, size, values):
    if i == 0:
        return (values[i][j-stride] +
                values[i][j+stride] +
                values[size-stride][j] +
                values[i+stride][j]) * 0.25
    elif i == size:
        return (values[i][j-stride] +
                values[i][j+stride] +
                values[i-stride][j] +
                values[stride][j]) * 0.25
    elif j == 0:
        return (values[i-stride][j] +
                values[i+stride][j] +
                values[i][j+stride] +
                values[i][size-stride]) * 0.25
    elif j == size:
        return (values[i-stride][j] +
                values[i+stride][j] +
                values[i][j-stride] +
                values[i][stride]) * 0.25
    else:
        return (values[i-stride][j] +
                values[i+stride][j] +
                values[i][j-stride] +
                values[i][j+stride]) * 0.25

#============================================================================#
#=================================================================== CLASS ==#
class World(object):
    def __init__(self, size):
        self.octree = core.Octree(size)
        self.mesh = None

    def generate_terrain(self):
        """generates a height map using the diamond-square algorithm
        and then assembles an Octree using the height map
        """
        stime = time.time()

        size = int(self.octree.size())
        values = numpy.zeros((size+1, size+1), dtype=float)
        sea_level = 0.0
        ratio = 0.5
        scale = float(size) / 8.0
        stride = size / 2

        random.seed(1234)
        while stride:
            # perform 'square' step
            #
            for i in xrange(stride, size, stride*2):
                for j in xrange(stride, size, stride*2):
                    values[i][j] = scale * fractal_rand() + avg_square_vals(i, j, stride, values)

            # perform 'diamond' step
            #
            oddline = False
            for i in xrange(0, size, stride):
                oddline = (oddline is False)
                start = 0
                if oddline:
                    start = stride
                for j in xrange(start, size, stride*2):
                    values[i][j] = scale * fractal_rand() + avg_diamond_vals(i, j, stride, size, values)

                    if i == 0:
                        values[size][j] = values[i][j]
                    if j == 0:
                        values[i][size] = values[i][j]

            scale *= ratio
            stride >>= 1

        print 'generation time:', (time.time() - stime)

        stime = time.time()
        self.octree.initialize_from_height_map(values)
        print 'adding points time:', (time.time() - stime)

        # # create a debug mesh that represents the heightmap
        # #
        # stime = time.time()
        # start_x = -(self.octree.size() / 2)
        # start_z = -(self.octree.size() / 2)
        # for x, row in enumerate(values[:-1]):
        #     x = start_x + float(x) + 0.5
        #     for z, y in enumerate(row[:-1]):
        #         z = start_z + float(z) + 0.5
        #         top = self.octree.get_height(x,z)
        #         bottom = top - 1.0
        #         if y > top or y <= bottom:
        #             print '(%s, %s): y=%f, top=%s, bottom=%s' % (x,z,y,top,bottom)



        # from ..data import cube
        # from ..core import Mesh
        # index_offset = 0
        # verts = []
        # normals = []
        # indices = []
        # start_x = -(self.octree.size() / 2)
        # start_z = -(self.octree.size() / 2)
        # for x, row in enumerate(values[:-1]):
        #     x = start_x + float(x) + 0.5
        #     for z, y in enumerate(row[:-1]):
        #         z = start_z + float(z) + 0.5

        #         # VERTS = cube.VERTICES
        #         # for i in xrange(12, 24, 3):
        #         #     verts.append(x+VERTS[i])
        #         #     verts.append(y+VERTS[i+1])
        #         #     verts.append(z+VERTS[i+2])
        #         # normals += cube.NORMALS[12:24]
        #         # faces = [0,1,3,2,3,1]
        #         # indices += [i + index_offset for i in faces]
        #         # index_offset += 4

        #         VERTS = cube.VERTICES
        #         for i in xrange(0, len(VERTS), 3):
        #             verts.append(x+VERTS[i])
        #             verts.append(y+VERTS[i+1])
        #             verts.append(z+VERTS[i+2])
        #         normals += cube.NORMALS
        #         indices += [i + index_offset for i in cube.INDICES]
        #         index_offset += len(VERTS)/3

        # self._debug_mesh = Mesh(verts, normals, indices, GL.GL_TRIANGLES)
        # print 'debugging time:', (time.time() - stime)

        stime = time.time()
        self.generate_terrain_mesh()
        print 'mesh generation time:', (time.time() - stime)

    def generate_terrain_mesh(self):
        self.mesh = self.octree.generate_mesh()

    def render(self, game, shader):
        GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 1.0, 0.5, 1.0)
        self.mesh.render()

        # # render the debug mesh
        # #
        # GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
        # self._debug_mesh.render()


