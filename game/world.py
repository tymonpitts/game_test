#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math

import numpy
import glfw
import noise

from .. import core

#============================================================================#
#=================================================================== CLASS ==#
class World(object):
    def __init__(self, size):
        self.octree = core.Octree(size)

    def generate_terrain(self):
        size = int(self.octree.size() * 0.5)
        for x in xrange(-size, size):
            x = float(x) + 0.5
            for z in xrange(-size, size):
                z = float(z) + 0.5
                value = noise.snoise2(x,z)
                height = int(float(size) * value)
                for y in xrange(-size,height):
                    y = float(y) + 0.5
                    print 'adding %s %s %s' % (x, y, z)
                    self.octree.add_point((x,y,z), point_data=100)
                    print 'DONE - adding %s %s %s' % (x, y, z)

    def render(self, game, shader, matrix_stack):
        self.octree.render(game, shader, matrix_stack)

