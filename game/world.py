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
        sea_level = size * 0.5
        for x in xrange(-size, size):
            x = float(x) + 0.5
            for z in xrange(-size, size):
                z = float(z) + 0.5
                noise_x = x * 0.001
                noise_z = z * 0.001
                value = noise.snoise2(noise_x, noise_z, octaves=100, lacunarity=10.0)
                value *= 8.0
                height = int(sea_level + value)
                # height = int(float(size) * value)
                for y in xrange(-size,height):
                    y = float(y) + 0.5
                    # print 'adding %s %s %s' % (x, y, z)
                    self.octree.add_point((x,y,z), point_data=100)
                    # print 'DONE - adding %s %s %s' % (x, y, z)
        # self.octree.add_point((), 100)

    def render(self, game, shader):
        self.octree.render(game, shader)

