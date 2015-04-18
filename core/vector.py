__all__ = ['Vector']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy

from .abstract_vector import AbstractVector


#============================================================================#
#=================================================================== CLASS ==#
class Vector(AbstractVector):
    def length(self):
        return numpy.linalg.norm(self)

    def normalize(self):
        length = self.length()
        if length == 0:
            return
        self /= length

    def normal(self):
        copy = self.copy()
        copy.normalize()
        return copy

    def __xor__(self, other):
        data = numpy.cross(self, other)
        return type(self)(*data)

    def __rxor__(self, other):
        data = numpy.cross(other, self)
        return type(self)(data)

    def dot(self, other):
        return numpy.dot(self, other)

    def magnitude(self):
        result = 0
        for c in self:
            result += pow(c, 2)
        return math.sqrt(result)

