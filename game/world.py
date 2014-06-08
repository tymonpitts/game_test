#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import random

import numpy
import glfw
import noise

from .. import core

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

    def generate_terrain(self):
        size = int(self.octree.size())
        values = numpy.ndarray((size+1, size+1), dtype=float)
        sea_level = 0.0
        ratio = 0.8
        scale = 1.0
        stride = size / 2
        values[0][0] = 0.0

        while stride:
            # print '-------------------------'
            grid = [['.' for j in xrange(size+1)] for i in xrange(size+1)]

            for i in xrange(stride, size, stride*2):
                for j in xrange(stride, size, stride*2):
                    grid[i][j] = 'x'
                    values[i][j] = scale * fractal_rand() + avg_square_vals(i, j, stride, values)

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
                    values[i][j] = scale * fractal_rand() + avg_diamond_vals(i, j, stride, size, values)

                    if i == 0:
                        grid[size][j] = 'x'
                        values[size][j] = values[i][j]
                    if j == 0:
                        grid[i][size] = 'x'
                        values[i][size] = values[i][j]

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

        half_size = size / 2
        for i in xrange(1, size+1):
            x = float(i) - float(half_size) - 0.5
            for j in xrange(1, size+1):
                z = float(j) - float(half_size) - 0.5
                v = avg_vals(i, j, values) * (float(size) / 8.0)
                height = int(round(v))
                height = clamp(height, -half_size+1, half_size)
                for y in xrange(-half_size+1, height+1):
                    y = float(y) - 0.5
                    self.octree.add_point((x,y,z), 100)

    def render(self, game, shader):
        self.octree.render(game, shader)

