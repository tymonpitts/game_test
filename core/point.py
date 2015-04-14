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
    @property
    def w(self):
        return 1.0

