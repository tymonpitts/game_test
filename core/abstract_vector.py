__all__ = ['AbstractVector']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy

#============================================================================#
#=================================================================== CLASS ==#
class AbstractVector(object):
    def __init__(self, x=0, y=0, z=0, w=0, other=None, data=None):
        if other:
            x = other.x
            y = other.y
            z = other.z
        if data is not None:
            self._data = data.copy()
        else:
            self._data = numpy.matrix([[x, y, z, w]], dtype=float)

    def copy(self):
        return type(self)(data=self._data)

    @property
    def x(self):
        return self[0]

    @x.setter
    def x(self, value):
        self[0] = value

    @property
    def y(self):
        return self[1]

    @y.setter
    def y(self, value):
        self[1] = value

    @property
    def z(self):
        return self[2]

    @z.setter
    def z(self, value):
        self[2] = value

    @property
    def w(self):
        return self[3]

    @w.setter
    def w(self, value):
        self[3] = value

    def tolist(self):
        return self._data.tolist()[0]

    def __str__(self):
        return str(self.tolist())

    def __getitem__(self, index):
        return self._data.item(0, index)

    def __setitem__(self, index, value):
        self._data.itemset(0, index, value)

    def __add__(self, other):
        data = numpy.add(self._data, other._data)
        return type(self)(data=data)

    def __iadd__(self, other):
        self._data = numpy.add(self._data, other._data)
        return self

    def __sub__(self, other):
        data = numpy.subtract(self._data, other._data)
        return type(self)(data=data)

    def __isub__(self, other):
        self._data = numpy.subtract(self._data, other._data)
        return self

    def __mul__(self, other):
        data = self._data * other._data
        return type(self)(data=data)

    def __imul__(self, other):
        if hasattr(other, '_data'):
            self._data *= other._data
        else:
            self._data *= other
        return self

    def __iter__(self):
        for item in self._data:
            yield item

