__all__ = ['Matrix', 'MatrixStack']

import math

import numpy
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from .vector import Vector


class Matrix(object):
    def __init__(self, other=None):
        from . import Quaternion
        if other is None:
            self._data = numpy.matrix([
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]], dtype=float)
        elif isinstance(other, numpy.matrix):
            self._data = other
        elif isinstance(other, Matrix):
            self._data = other._data.copy()
        elif isinstance(other, Quaternion):
            self._data = numpy.matrix([
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]], dtype=float)
            other.as_matrix(self)
        else:
            TypeError('Unable to cast %s to Matrix' % type(other))

    @classmethod
    def from_axis_vectors(cls, x=None, y=None, z=None):
        # type: (Optional[Vector], Optional[Vector], Optional[Vector]) -> Matrix
        """ compute a rotation matrix from the provided axis vectors
        (i.e. each vector is orthogonal to each other vector)

        Only 2 of the vectors are required since the third can be
        derived from the other 2

        Args:
            x (Optional[Vector]): vector representing the x-axis the matrix should rotate into
            y (Optional[Vector]): vector representing the y-axis the matrix should rotate into
            z (Optional[Vector]): vector representing the z-axis the matrix should rotate into

        Returns:
            Matrix: a transform matrix that will rotate into the provided coordinate system
        """
        axes = [x, y, z]
        if axes.count(None) > 1:
            raise Exception('need at least 2 axes to compute a rotation matrix')
        elif x is None:
            x = y ^ z
        elif y is None:
            y = z ^ x
        elif z is None:
            z = x ^ y

        result = cls()
        for i in range(3):
            result[0, i] = x[i]
            result[1, i] = y[i]
            result[2, i] = z[i]
        return result

    def as_quaternion(self):
        from . import Quaternion
        q = Quaternion()
        tr = self[0,0] + self[1,1] + self[2,2]

        if tr > 0:
            S = math.sqrt(tr+1.0) * 2.0 # S=4*qw 
            q.w = 0.25 * S
            q.x = (self[2,1] - self[1,2]) / S
            q.y = (self[0,2] - self[2,0]) / S
            q.z = (self[1,0] - self[0,1]) / S
        elif self[0,0] > self[1,1] and self[0,0] > self[2,2]:
            S = math.sqrt(1.0 + self[0,0] - self[1,1] - self[2,2]) * 2.0 # S=4*qx 
            q.w = (self[2,1] - self[1,2]) / S
            q.x = 0.25 * S
            q.y = (self[0,1] + self[1,0]) / S
            q.z = (self[0,2] + self[2,0]) / S
        elif self[1,1] > self[2,2]:
            S = math.sqrt(1.0 + self[1,1] - self[0,0] - self[2,2]) * 2.0 # S=4*qy
            q.w = (self[0,2] - self[2,0]) / S
            q.x = (self[0,1] + self[1,0]) / S
            q.y = 0.25 * S
            q.z = (self[1,2] + self[2,1]) / S
        else:
            S = math.sqrt(1.0 + self[2,2] - self[0,0] - self[1,1]) * 2.0 # S=4*qz
            q.w = (self[1,0] - self[0,1]) / S
            q.x = (self[0,2] + self[2,0]) / S
            q.y = (self[1,2] + self[2,1]) / S
            q.z = 0.25 * S

        return q

    def transpose(self):
         return type(self)(numpy.transpose(self._data))

    def copy(self):
        return Matrix(self._data.copy())

    @classmethod
    def sizeof(cls):
        if isinstance(cls, Matrix):
            self = cls
        else:
            self = cls()
        return self._data.nbytes

    def tolist(self):
        return self._data.tolist()

    def inverse(self):
        return type(self)(self._data.I)

    def __getitem__(self, index):
        if not hasattr(index, '__iter__'):
            raise IndexError('index must be a sequence, not %s' % type(index).__name__)
        return self._data.item(*index)

    def __setitem__(self, index, value):
        if not hasattr(index, '__iter__'):
            raise IndexError('index must be a sequence, not %s' % type(index).__name__)
        self._data.itemset(index[0], index[1], value)

    def __mul__(self, other):
        return Matrix(numpy.dot(self._data, other._data))

    def __imul__(self, other):
        self._data = numpy.dot(self._data, other._data)
        return self

    def __str__(self):
        l = self.tolist()
        result = ''
        result += '\t' + str(l[0]) + '\n'
        result += '\t' + str(l[1]) + '\n'
        result += '\t' + str(l[2]) + '\n'
        result += '\t' + str(l[3]) + '\n'
        return result

    def rotateX(self, fAngDeg):
        fAngRad = math.radians(fAngDeg)
        fCos = math.cos(fAngRad)
        fSin = math.sin(fAngRad)

        mat = Matrix()
        mat[1,1] = fCos
        mat[1,2] = fSin
        mat[2,1] = -fSin
        mat[2,2] = fCos

        mat *= self
        self._data = mat._data

    def rotateY(self, fAngDeg):
        fAngRad = math.radians(fAngDeg)
        fCos = math.cos(fAngRad)
        fSin = math.sin(fAngRad)

        mat = Matrix()
        mat[0,0] = fCos
        mat[0,2] = -fSin
        mat[2,0] = fSin
        mat[2,2] = fCos

        mat *= self
        self._data = mat._data

    def rotateZ(self, fAngDeg):
        fAngRad = math.radians(fAngDeg)
        fCos = math.cos(fAngRad)
        fSin = math.sin(fAngRad)

        mat = Matrix()
        mat[0,0] = fCos
        mat[0,1] = fSin
        mat[1,0] = -fSin
        mat[1,1] = fCos

        mat *= self
        self._data = mat._data

    def scale(self, scaleVec):
        if not hasattr(scaleVec, '__iter__'):
            scaleVec = [scaleVec] * 3
        mat = Matrix()
        for index in xrange(3):
            mat[index, index] = scaleVec[index]

        mat *= self
        self._data = mat._data

    def translate(self, offsetVec):
        if not hasattr(offsetVec, '__iter__'):
            offsetVec = [offsetVec] * 3
        mat = Matrix()
        for index in xrange(3):
            mat[3, index] = offsetVec[index]

        mat *= self
        self._data = mat._data

class MatrixStack(object):
    def __init__(self):
        self.m_currMat = Matrix()
        self.m_matrices = []
        self.__enter_lengths = []

    def __enter__(self):
        self.__enter_lengths.append(len(self.m_matrices))

    def __exit__(self, typ, val, tb):
        enter_len = self.__enter_lengths.pop()
        self.m_matrices = self.m_matrices[:enter_len]
        if self.m_matrices:
            self.m_currMat = self.m_matrices[-1]
        else:
            self.m_currMat = Matrix()

    def top(self):
        return self.m_currMat

    def rotateX(self, fAngDeg):
        self.m_currMat.rotateX(fAngDeg)
        self.push()

    def rotateY(self, fAngDeg):
        self.m_currMat.rotateY(fAngDeg)
        self.push()

    def rotateZ(self, fAngDeg):
        self.m_currMat.rotateZ(fAngDeg)
        self.push()

    def scale(self, scaleVec):
        self.m_currMat.scale(scaleVec)
        self.push()

    def translate(self, offsetVec):
        self.m_currMat.translate(offsetVec)
        self.push()

    def push(self):
        self.m_matrices.append(self.m_currMat.copy())

    def pop(self):
        result = self.m_matrices.pop()
        if len(self.m_matrices):
            self.m_currMat = self.m_matrices[-1].copy()
        else:
            self.m_currMat = Matrix()
        return result

    def perspective(self, fovy, aspect, zNear, zFar):
        range = math.tan(math.radians(fovy)/2.0) * zNear
        left = -range * aspect
        right = range * aspect
        bottom = -range
        top = range

        result = Matrix()
        result[0,0] = (2.0 * zNear) / (right - left)
        result[1,1] = (2.0 * zNear) / (top - bottom)
        result[2,2] = -(zFar + zNear) / (zFar - zNear)
        result[2,3] = -1.0
        result[3,2] = -(2.0 * zFar * zNear) / (zFar - zNear)

        self.m_currMat = result * self.m_currMat
        self.push()

