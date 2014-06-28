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

    def _print_values(self, values):
        with Logger('values:'):
            for row in values[:-1]:
                message = ''
                for v in row[:-1]:
                    message += '%f ' % v
                log(message)

    def generate_terrain(self):
        stime = time.time()

        size = int(self.octree.size())
        values = numpy.zeros((size+1, size+1), dtype=float)
        # values = numpy.ndarray((size+1, size+1), dtype=float)
        sea_level = 0.0
        ratio = 0.8
        scale = float(size) / 8.0
        stride = size / 2
        values[0][0] = 0.0

        print 'size: %s' % size
        print 'stride: %s' % stride
        # self._print_values(values)

        random.seed(1234)
        while stride:
            # print '-------------------------'
            grid = [['.' for j in xrange(size+1)] for i in xrange(size+1)]

            for i in xrange(stride, size, stride*2):
                for j in xrange(stride, size, stride*2):
                    grid[i][j] = 'x'
                    fr = fractal_rand()
                    asv = avg_square_vals(i, j, stride, values)
                    values[i][j] = scale * fr + asv
                    # values[i][j] = scale * fractal_rand() + avg_square_vals(i, j, stride, values)

                    # log('fr: %s' % fr)
                    # log('asv: %s' % asv)
                    # log('values[%s][%s]: %s' % (i, j, values[i][j]))
                    # log('')

            # for row in grid:
            #     for char in row:
            #         print char,
            #     print
            # print

            grid = [['.' for j in xrange(size+1)] for i in xrange(size+1)]

            oddline = False
            for i in xrange(0, size, stride):
                oddline = (oddline is False)
                start = 0
                if oddline:
                    start = stride
                for j in xrange(start, size, stride*2):
                    grid[i][j] = 'x'
                    fr = fractal_rand()
                    adv = avg_diamond_vals(i, j, stride, size, values)
                    values[i][j] = scale * fr + adv
                    # values[i][j] = scale * fractal_rand() + avg_diamond_vals(i, j, stride, size, values)

                    # log('fr: %s' % fr)
                    # log('adv: %s' % adv)
                    # log('values[%s][%s]: %s' % (i, j, values[i][j]))
                    # log('')

                    if i == 0:
                        grid[size][j] = 'x'
                        values[size][j] = values[i][j]
                    if j == 0:
                        grid[i][size] = 'x'
                        values[i][size] = values[i][j]

            # self._print_values(values)
            # log('')

            # for row in grid:
            #     for char in row:
            #         print char,
            #     print
            # print

            scale *= ratio
            stride >>= 1

        # for row in values:
        #     for v in row:
        #         print '%5f' % v,
        #     print
        # print

        print 'generation time:', (time.time() - stime)


        # self._print_values(values)

        stime = time.time()

        # half_size = size / 2
        # for i in xrange(1, size+1):
        #     x = float(i) - float(half_size) - 0.5
        #     for j in xrange(1, size+1):
        #         z = float(j) - float(half_size) - 0.5
        #         v = avg_vals(i, j, values) * (float(size) / 8.0)
        #         height = int(round(v))
        #         height = clamp(height, -half_size+1, half_size)
        #         for y in xrange(-half_size+1, height+1):
        #             y = float(y) - 0.5
        #             self.octree.add_point((x,y,z), 100)
        #         # y = float(height) - 0.5
        #         # self.octree.add_point((x,y,z), 100)
        self.octree.initialize_from_height_map(values)


        # start_x = -(self.octree.size() / 2)
        # start_z = -(self.octree.size() / 2)
        # for x, row in enumerate(self._values[:-1]):
        #     x = start_x + float(x) + 0.5
        #     for z, y in enumerate(row[:-1]):
        #         z = start_z + float(z) + 0.5
        #         top = self.octree.get_height(x,z)
        #         bottom = top - 1.0
        #         if y > top or y <= bottom:
        #             print '(%s, %s): y=%f, top=%s, bottom=%s' % (x,z,y,top,bottom)

        # self._print_values(values)

        print 'adding points time:', (time.time() - stime)

        stime = time.time()
        self.generate_terrain_mesh()
        print 'mesh generation time:', (time.time() - stime)

    def generate_terrain_mesh(self):
        self.mesh = self.octree.generate_mesh()

    def render(self, game, shader):
        GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 1.0, 0.5, 0.5)
        self.mesh.render()
        # GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 1.0, 1.0)
        # self.octree.render(game, shader)


