__all__ = ['Octree']

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

from .logger import log, increase_tab, decrease_tab, Logger

#============================================================================#
#=================================================================== CLASS ==#
class AbstractOctree(object):
    def _is_leaf(self):
        return False

    def data(self):
        return None

class AbstractOctreeParent(AbstractOctree):
    def _get_child_info(self, info, index, copy=True):
        if copy:
            info = info.copy()
            info['origin'] = info['origin'].copy()
            info['parents'] = list(info.get('parents', []))
        info['level'] += 1
        info['size'] *= 0.5
        info['index'] = index
        info['parents'].append(self)

        offset = Vector()
        offset.x = 0.5 if index&4 else -0.5
        offset.y = 0.5 if index&2 else -0.5
        offset.z = 0.5 if index&1 else -0.5

        offset *= info['size']
        info['origin'] += offset

        return info

    def children(self):
        return self._children

    def child(self, index):
        return self._children[index]

    def iter_children_info(self, info):
        for index, child in enumerate(self._children):
            yield (child, self._get_child_info(info, index))

    def _get_point(self, point, info):
        index = self._child_index_closest_to_point(point, info['origin'])
        return self.child(index)._get_point(point, self._get_child_info(info, index))

    def _get_height(self, x, z, info):
        origin = info['origin']
        index1 = 0
        if x >= origin.x: index1 |= 4
        if z >= origin.z: index1 |= 1
        index2 = index1
        index1 |= 2

        child1 = self.child(index1)
        height = child1._get_height(x,z,self._get_child_info(info, index1))
        if height is not None:
            return height

        child2 = self.child(index2)
        return child2._get_height(x,z,self._get_child_info(info, index2))

    def _child_index_closest_to_point(self, point, origin):
        index = 0
        if point.x >= origin.x: index |= 4
        if point.y >= origin.y: index |= 2
        if point.z >= origin.z: index |= 1

        return index

    def _should_neighbor_generate_mesh(self, info, indices):
        for index in indices:
            child = self.child(index)
            child_info = self._get_child_info(info)
            if _should_neighbor_generate_mesh(child_info, indices):
                return True
        return False

    def _generate_mesh(self, info):
        verts = []
        normals = []
        indices = []
        for child, child_info in self.iter_children_info(info):
            result = child._generate_mesh(child_info)
            if result is None:
                continue
            c_verts, c_normals, c_indices = result
            info['index_offset'] += len(c_verts)/3
            verts.extend(c_verts)
            normals.extend(c_normals)
            indices.extend(c_indices)
        return verts, normals, indices

    def _init_column_from_height_map(self, values, indices, min_height, max_height, origin, info):
        max_ = values.max()
        min_ = values.min()
        all_leaf = (len(values) == 1)

        # handle cases where both children are either solid or empty
        #
        if min_ > max_height:
            self._children[indices[0]] = OctreeLeaf(1)
            self._children[indices[1]] = OctreeLeaf(1)
            return
        elif max_ <= min_height:
            self._children[indices[0]] = OctreeLeaf(0)
            self._children[indices[1]] = OctreeLeaf(0)
            return

        # handle top
        #
        if max_ <= origin:
            self._children[indices[0]] = OctreeLeaf(0)
        elif all_leaf:
            self._children[indices[0]] = OctreeLeaf(1)
        else:
            self._children[indices[0]] = OctreeInterior()
            self._children[indices[0]]._init_from_height_map(values, self._get_child_info(info, indices[0]))

        # handle bottom
        #
        if min_ > origin or all_leaf:
            self._children[indices[1]] = OctreeLeaf(1)
        else:
            self._children[indices[1]] = OctreeInterior()
            self._children[indices[1]]._init_from_height_map(values, self._get_child_info(info, indices[1]))

    def _init_from_height_map(self, values, info):
        # gather data to initialize each column individually
        #
        self._children = [None] * 8
        full_size = len(values)
        size = full_size / 2
        origin = info['origin'].y
        min_height = origin - (info['size']/2)
        max_height = origin + (info['size']/2)

        """
        x o
        o o
        """
        v = values[:size, :size]
        indices = (2, 0) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, info)

        """
        o x
        o o
        """
        v = values[size:full_size, :size]
        indices = (6, 4) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, info)

        """
        o o
        x o
        """
        v = values[:size, size:full_size]
        indices = (3, 1) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, info)

        """
        o o
        o x
        """
        v = values[size:full_size, size:full_size]
        indices = (7, 5) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, info)

class AbstractOctreeChild(AbstractOctree):
    pass

class Octree(AbstractOctreeParent):
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
        super(Octree, self).__init__()
        self._size = size
        self._children = tuple([OctreeLeaf(self) for i in xrange(8)])

    def _get_info(self):
        info = {}
        info['level'] = 1
        info['size'] = self.size()
        info['origin'] = self.origin()
        return info

    def origin(self):
        return Point()

    def size(self):
        return self._size

    def generate_mesh(self):
        from ..data import cube
        from . import Mesh
        info = self._get_info()
        info['cube'] = cube
        info['index_offset'] = 0
        verts, normals, indices = self._generate_mesh(info)
        return Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def initialize_from_height_map(self, values):
        values = values[:-1, :-1]
        self._init_from_height_map(values, self._get_info())

    def get_height(self, x, z):
        return self._get_height(x,z,self._get_info())

    def get_point(self, point):
        half_size = self.size() / 2.0
        for i in xrange(3):
            if abs(point[i]) > half_size:
                return (None, None)
        return self._get_point(point, self._get_info())

class OctreeInterior(AbstractOctreeParent, AbstractOctreeChild):
    def __init__(self):
        # self._children = tuple([OctreeLeaf(self) for i in xrange(8)])
        pass

class OctreeLeaf(AbstractOctreeChild):
    def __init__(self, data=None):
        self._data = data

    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data
        # TODO: possibly merge here

    def _get_point(self, point, info):
        return self, info

    def _get_height(self, x, z, info):
        if not self.data():
            return None
        return info['origin'].y+0.5

    def _is_leaf(self):
        return True

    def _should_neighbor_generate_mesh(self, info, indices):
        return not bool(self.data())

    def _should_generate_mesh__check_neighbor(self, info, axis, direction, indices):
        """check if this neighbor is transparent
        """
        origin = info['origin']
        size = info['size']

        point = origin.copy()
        point[axis] += size*direction
        obj, obj_info = info['parents'][0].get_point(point)

        if obj is None:
            return True
        elif obj._should_neighbor_generate_mesh(obj_info, indices):
            return True
        return False

    def _should_generate_mesh(self, info):
        return bool(self.data())
        # if not self.data():
        #     return False

        # if self._should_generate_mesh__check_neighbor(info, 0, 1.0, [6,7,4,5]): # +x
        #     return True
        # elif self._should_generate_mesh__check_neighbor(info, 0, -1.0, [2,3,0,1]): # -x
        #     return True
        # elif self._should_generate_mesh__check_neighbor(info, 1, 1.0, [2,3,6,7]): # +y
        #     return True
        # elif self._should_generate_mesh__check_neighbor(info, 1, -1.0, [0,1,4,5]): # -y
        #     return True
        # elif self._should_generate_mesh__check_neighbor(info, 2, 1.0, [2,6,0,4]): # +z
        #     return True
        # elif self._should_generate_mesh__check_neighbor(info, 2, -1.0, [3,7,1,5]): # -z
        #     return True
        # return False

    def _generate_mesh(self, info):
        if not self._should_generate_mesh(info):
            return

        # generate mesh data for this point
        #
        origin = info['origin']
        size = info['size']
        VERTS = info['cube'].VERTICES
        verts = []
        for i in xrange(0, len(VERTS), 3):
            # vert = origin + Vector([VERTS[i], VERTS[i+1], VERTS[i+2]]) * size
            # verts.append(vert.x)
            # verts.append(vert.y)
            # verts.append(vert.z)
            verts.append(origin.x + VERTS[i] * size)
            verts.append(origin.y + VERTS[i+1] * size)
            verts.append(origin.z + VERTS[i+2] * size)
        normals = info['cube'].NORMALS
        indices = [i + info['index_offset'] for i in info['cube'].INDICES]
        return verts, normals, indices

