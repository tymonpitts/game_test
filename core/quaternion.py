__all__ = ['Quaternion']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy


#============================================================================#
#=================================================================== CLASS ==#
class Quaternion(object):
    def __init__(self, *args):
        from . import Matrix
        if len(args) == 0:
            self._data = numpy.array([0,0,0,0], dtype=float)
        elif len(args) == 1 and isinstance(args[0], Matrix):
            self._data = numpy.array([0,0,0,0], dtype=float)
            args[0].as_quaternion(self)
        # elif len(args) == 1:
        #     from .abstract_vector import AbstractVector
        #     if isinstance(args[0], AbstractVector):
        #         data = [item for item in args[0]]
        #         data += [0.0]
        #     elif len(args[0]) > 4:
        #         data = [args[0][i] for i in xrange(4)]
        #     else:
        #         data = [item for item in args[0]]
        #         data += [0.0] * (4-len(args[0]))
        #     self._data = numpy.array(data, dtype=float)
        else:
            ValueError('Unable to cast args to Quaternion: %s' % args)

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

    def __getitem__(self, index):
        return self._data.item(index)

    def __setitem__(self, index, value):
        self._data.itemset(index, value)

    def length(self):
        return numpy.linalg.norm(self._data)

    def normalize(self):
        self._data /= self.length()

    def normal(self):
        result = Quaternion()
        result._data = self._data / self.length()
        return result

    def __mul__(self, other):
        from . import Vector
        if isinstance(other, Vector):
            return self.vector_mult(other)
        result = Quaternion(other=self)
        result *= other
        return result

    def __imul__(self, other):
        w1 = self.w
        x1 = self.x
        y1 = self.y
        z1 = self.z

        w1 = other.w
        x1 = other.x
        y1 = other.y
        z1 = other.z

        self.w = w1 * w2 - x1 * x2 - y1 * y2 - z1 * z2
        self.x = w1 * x2 + x1 * w2 + y1 * z2 - z1 * y2
        self.y = w1 * y2 + y1 * w2 + z1 * x2 - x1 * z2
        self.z = w1 * z2 + z1 * w2 + x1 * y2 - y1 * x2
        return self

    def conjugate(self):
        q = self.normal()
        q.x = -q.x
        q.y = -q.y
        q.z = -q.z
        return q

    def vector_mult(self, v):
        from . import Vector
        v = v.normal()
        v = Quaternion(v.x, v.y, v.z)
        result = self * v * self.conjugate()
        return result.as_vector()

    def get_axis_angle(self):
        angle = math.acos(self.w) * 2.0
        return (self.as_vector(), angle)

    def set_axis_angle(self, v, angle):
        v = v.normal()
        angle /= 2.0
        sin_angle = math.sin(angle)
        self.w = math.cos(angle)
        self.x = v.x * sin_angle
        self.y = v.y * sin_angle
        self.z = v.z * sin_angle
        return self

    def as_vector(self, v=None):
        if v is None:
            from . import Vector
            return Vector(self.x, self.y, self.z)
        else:
            v.x = self.x
            v.y = self.y
            v.z = self.z
            return v

    def as_matrix(self, m=None):
        if m is None:
            from . import Matrix
            m = Matrix()
        x = self.x
        y = self.y
        z = self.z
        w = self.w

        x_sq = x * x
        y_sq = y * y
        z_sq = z * z

        m[0,0] = 1.0 - (2.0 * y_sq) - (2.0 * z_sq) 
        m[0,1] = (2.0 * x * y) + (2.0 * w * z) 
        m[0,2] = (2.0 * x * z) - (2.0 * w * y) 

        m[1,0] = (2.0 * x * y) - (2.0 * w * z) 
        m[1,1] = 1.0 - (2.0 * x_sq) - (2.0 * z_sq) 
        m[1,2] = (2.0 * y * z) + (2.0 * w * x) 

        m[2,0] = (2.0 * x * z) + (2.0 * w * y) 
        m[2,1] = (2.0 * y * z) - (2.0 * w * x)
        m[2,2] = 1.0 - (2.0 * x_sq) - (2.0 * y_sq)

        return m





