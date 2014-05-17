__all__ = ['Point']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy

from .abstract_vector import AbstractVector

#============================================================================#
#=================================================================== CLASS ==#
class Point(AbstractVector):
    def __init__(self, x=0, y=0, z=0, w=1, other=None, data=None):
        super(Point, self).__init__(x, y, z, w, other, data)

    def __add__(self, other):
        result = super(Point, self).__add__(other)
        return Vector(result[0], result[1], result[2])

    def __sub__(self, other):
        result = super(Point, self).__sub__(other)
        return Vector(result[0], result[1], result[2])

