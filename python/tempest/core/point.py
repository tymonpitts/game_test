from .abstract_vector import AbstractVector
import numpy

__all__ = ['Point']

class Point(AbstractVector):
    @property
    def w(self):
        return 1.0

    def distance(self, other):
        return numpy.linalg.norm(self - other)
