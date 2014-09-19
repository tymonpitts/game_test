__all__ = ['AbstractTree']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy
import random

from OpenGL import GL

from . import Point
from . import Vector
from . import Matrix
from . import BoundingBox

from .logger import log, increase_tab, decrease_tab, Logger

#============================================================================#
#=================================================================== CLASS ==#
class AbstractTreeBase(object):
    @property
    def _leaf_cls(self):
        return AbstractTreeLeaf

    @property
    def _interior_cls(self):
        return AbstractTreeInterior

    def _is_leaf(self):
        return False

    def data(self):
        return None

class AbstractTreeInterior(AbstractTreeBase):
    def _get_child_info(self, info, index, copy=True):
        if copy:
            info = info.copy()
            info['origin'] = info['origin'].copy()
            info['parents'] = list(info['parents'])
        info['level'] += 1
        info['size'] *= 0.5
        info['index'] = index
        info['parents'].append(self)

        half_size = info['size'] * 0.5
        offset = [0.0, 0.0, 0.0]
        offset[0] = half_size if index&4 else -half_size
        offset[1] = half_size if index&2 else -half_size
        offset[2] = half_size if index&1 else -half_size

        for i, component in enumerate(offset):
            info['origin'][i] += component

        return info

    def children(self):
        return self._children

    def child(self, index):
        return self._children[index]

    def iter_children_info(self, info):
        for index, child in enumerate(self._children):
            yield (child, self._get_child_info(info, index))

    def _get_point(self, info, point):
        index = self._child_index_closest_to_point(info, point)
        return self.child(index)._get_point(self._get_child_info(info, index), point)

    def _child_index_closest_to_point(self, info, point):
        index = 0
        origin = info['origin']
        if point.x >= origin.x: index |= 4
        if point.y >= origin.y: index |= 2
        if point.z >= origin.z: index |= 1

        return index

class AbstractTreeLeaf(AbstractTreeBase):
    def __init__(self, data=None):
        self._data = data

    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data
        # TODO: possibly merge here

    def _get_point(self, info, point):
        return self, info

    def _is_leaf(self):
        return True

class AbstractTree(AbstractTreeInterior):
    """

    Child indices:
        top:
            2 6
            3 7
        bottom:
            0 4
            1 5
    """
    def __init__(self, size):
        super(AbstractTree, self).__init__()
        self._size = size
        self._children = tuple([self._leaf_cls(self) for i in xrange(8)])

    def _get_info(self):
        info = {}
        info['level'] = 1
        info['size'] = self.size()
        info['origin'] = self.origin()
        info['parents'] = [self]
        return info

    def origin(self):
        return Point()

    def size(self):
        return self._size

    def get_point(self, point):
        half_size = self.size() / 2.0
        for i in xrange(3):
            if abs(point[i]) > half_size:
                return (None, None)
        return self._get_point(self._get_info(), point)

