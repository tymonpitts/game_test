__all__ = ['Matrix', 'MatrixStack']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy

#============================================================================#
#=================================================================== CLASS ==#
class Matrix(object):
    def __init__(self, data=None):
        if data is not None:
            self._data = data.copy()
        else:
            self._data = numpy.matrix([
                    [1, 0, 0, 0],
                    [0, 1, 0, 0],
                    [0, 0, 1, 0],
                    [0, 0, 0, 1]], dtype=float)

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
         data = numpy.transpose(self._data)
         return type(self)(data=data)

    def copy(self):
        return Matrix(data=self._data)

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
        return type(self)(data=self._data.I)

    def __getitem__(self, index):
        if not hasattr(index, '__iter__'):
            raise IndexError('index must be a sequence, not %s' % type(index).__name__)
        return self._data.item(*index)

    def __setitem__(self, index, value):
        if not hasattr(index, '__iter__'):
            raise IndexError('index must be a sequence, not %s' % type(index).__name__)
        self._data.itemset(index[0], index[1], value)

    def __mul__(self, other):
        data = numpy.dot(self._data, other._data)
        return Matrix(data=data)

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
        fAngRad = math.radians(fAngDeg)
        fCos = math.cos(fAngRad)
        fSin = math.sin(fAngRad)

        theMat = Matrix()
        theMat[1,1] = fCos
        theMat[1,2] = fSin
        theMat[2,1] = -fSin
        theMat[2,2] = fCos

        self.m_currMat = theMat * self.m_currMat
        self.push()

    def rotateY(self, fAngDeg):
        fAngRad = math.radians(fAngDeg)
        fCos = math.cos(fAngRad)
        fSin = math.sin(fAngRad)

        theMat = Matrix()
        theMat[0,0] = fCos
        theMat[0,2] = -fSin
        theMat[2,0] = fSin
        theMat[2,2] = fCos

        self.m_currMat = theMat * self.m_currMat
        self.push()

    def rotateZ(self, fAngDeg):
        fAngRad = math.radians(fAngDeg)
        fCos = math.cos(fAngRad)
        fSin = math.sin(fAngRad)

        theMat = Matrix()
        theMat[0,0] = fCos
        theMat[0,1] = fSin
        theMat[1,0] = -fSin
        theMat[1,1] = fCos

        self.m_currMat = theMat * self.m_currMat
        self.push()

    def scale(self, scaleVec):
        scaleMat = Matrix()
        for index in xrange(3):
            scaleMat[index, index] = scaleVec[index]

        self.m_currMat = scaleMat * self.m_currMat
        self.push()

    def translate(self, offsetVec):
        translateMat = Matrix()
        for index in xrange(3):
            translateMat[3, index] = offsetVec[index]

        self.m_currMat = translateMat * self.m_currMat
        self.push()

    def push(self):
        self.m_matrices.append(self.m_currMat.copy())

    def pop(self):
        # self.m_currMat = self.m_matrices.pop()
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

