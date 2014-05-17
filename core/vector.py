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
        return numpy.linalg.norm(self._data)

    def normalize(self):
        self._data /= self.length()

    def normal(self):
        result = Vector()
        result._data = self._data / self.length()
        return result

    def __xor__(self, other):
        data = numpy.cross(
                [self[0], self[1], self[2]], 
                [other[0], other[1], other[2]])
        return type(self)(data[0], data[1], data[2])

    def __rxor__(self, other):
        data = numpy.cross(
                [other[0], other[1], other[2]],
                [self[0], self[1], self[2]])
        return type(self)(data[0], data[1], data[2])

    def dot(self, other):
        return numpy.dot(
                [self[0], self[1], self[2]], 
                [other[0], other[1], other[2]])

