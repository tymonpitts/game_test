__all__ = ['AbstractVector']

#============================================================================#
#================================================================= IMPORTS ==#
import numpy

#============================================================================#
#=================================================================== CLASS ==#
class AbstractVector(object):
    def __init__(self, x=0.0, y=0.0, z=0.0):
        self._data = [float(x), float(y), float(z)]

    @classmethod
    def cast(cls, other):
        if isinstance(other, cls):
            return other
        elif hasattr(other, '__iter__'):
            return cls(*other[:3])
        else:
            return cls(other)

    def copy(self):
        return type(self)(*self._data)

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
        return 0.0

    def __str__(self):
        return str(self._data)

    def __getitem__(self, index):
        return self._data[index]

    def __setitem__(self, index, value):
        self._data[index] = float(value)

    def __neg__(self):
        return (self * -1.0)

    def __add__(self, other):
        result = self.copy()
        result += other
        return result

    def __iadd__(self, other):
        for i in xrange(len(self)):
            self._data[i] += other[i]
        return self

    def __sub__(self, other):
        result = self.copy()
        result -= other
        return result

    def __isub__(self, other):
        for i in xrange(len(self)):
            self._data[i] -= other[i]
        return self

    def _as_numpy_matrix(self):
        return numpy.matrix([[self.x, self.y, self.z, self.w]], dtype=float)

    def __mul__(self, other):
        result = self.copy()
        result *= other
        return result

    def __imul__(self, other):
        from . import Matrix
        if isinstance(other, Matrix):
            n_mat = self._as_numpy_matrix()
            n_mat = numpy.dot(n_mat, other._data)
            self._data = [n_mat.item(0, i) for i in xrange(3)]
        elif hasattr(other, '__iter__'):
            for i in xrange(3):
                self._data[i] *= other[i]
        else:
            for i in xrange(3):
                self._data[i] *= other
        return self

    def __div__(self, other):
        result = self.copy()
        result /= other
        return result

    def __idiv__(self, other):
        from . import Matrix
        if isinstance(other, Matrix):
            raise TypeError('unsupported operand type(s) for /: \'%s\' and \'%s\'' % (type(self), type(other)))
        elif hasattr(other, '__iter__'):
            for i in xrange(3):
                self._data[i] /= other[i]
        else:
            for i in xrange(3):
                self._data[i] /= other
        return self

    def __len__(self):
        return 3

    def __iter__(self):
        for item in self._data:
            yield item

    def __eq__(self, other):
        try:
            for i in xrange(len(self)):
                if self[i] != other[i]:
                    return False
            return True
        except:
            return False

    def __ne__(self, other):
        return (not self.__eq__(other))

    def round(self, decimals=6):
        for i in xrange(len(self)):
            self._data[i] = round(self._data[i], decimals)

