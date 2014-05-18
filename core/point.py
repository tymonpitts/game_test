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
    def _default_values(self):
        return [0,0,0,1]

    def __add__(self, other):
        result = super(Point, self).__add__(other)
        return Vector([result[0], result[1], result[2]])

    def __sub__(self, other):
        result = super(Point, self).__sub__(other)
        return Vector([result[0], result[1], result[2]])

