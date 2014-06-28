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

    def _copy_data(self, data):
        copied_data = data.copy()
        copied_data['origin'] = data['origin'].copy()
        return copied_data

    def data(self):
        return None

class AbstractOctreeParent(AbstractOctree):
    def data(self):
        return None

    def children(self):
        return self._children

    def _get_height(self, x, z, data):
        self._update_data(data)
        origin = data['origin']

        index1 = 0
        if x >= origin.x: index1 |= 4
        if z >= origin.z: index1 |= 1
        index2 = index1
        index1 |= 2

        child1 = self.children()[index1]
        height = child1._get_height(x,z,self._copy_data(data))
        if height is not None:
            return height

        child2 = self.children()[index2]
        return child2._get_height(x,z,self._copy_data(data))

    def _split_leaf(self, child):
        children = list(self.children())
        index = children.index(child)
        children.remove(child)
        new_child = OctreeInterior.from_leaf(child)
        for child in new_child.children():
            child.set_data(self.data())
        children.insert(index, new_child)
        self._children = tuple(children)
        return new_child

    def _child_containing_point(self, point, origin):
        index = 0
        if point.x >= origin.x: index |= 4
        if point.y >= origin.y: index |= 2
        if point.z >= origin.z: index |= 1

        return self.child(index)

    def child(self, index):
        return self._children[index]

    def _merge(self):
        new_node = OctreeLeaf(self.parent())
        data = self._children[0].data()
        new_node.set_data(data)

        children = list(self.parent()._children)
        index = children.index(self)
        children.remove(self)
        children.insert(index, new_node)
        self.parent()._children = tuple(children)
        return new_node

    def _add_point(self, point, point_data, data):
        self._update_data(data)
        # print '_add_point:', data['origin']
        child = self._child_containing_point(point, data['origin'])
        result = child._add_point(point, point_data, data)

        do_merge = True
        for child in self._children:
            if child.data() != result.data():
                do_merge = False
                break
        if do_merge:
            return self._merge()
        else:
            return result

    def _do_render(self, game, shader, data):
        for child in self._children:
            child_data = self._copy_data(data)
            child._render(game, shader, child_data)

    def _generate_mesh(self, data):
        self._update_data(data)
        verts = []
        normals = []
        indices = []
        for child in self._children:
            child_data = self._copy_data(data)
            result = child._generate_mesh(child_data)
            if result is None:
                continue
            c_verts, c_normals, c_indices = result
            data['index_offset'] += len(c_verts)/3
            verts.extend(c_verts)
            normals.extend(c_normals)
            indices.extend(c_indices)
        return verts, normals, indices

    def _init_column_from_height_map(self, values, indices, min_height, max_height, origin, data):
        max_ = values.max()
        min_ = values.min()
        all_leaf = (len(values) == 1)

        # log('min: %s' % min_)
        # log('max: %s' % max_)

        # handle cases where both children are either solid or empty
        #
        if min_ > max_height:
            self._children[indices[0]] = OctreeLeaf(self, 1)
            self._children[indices[1]] = OctreeLeaf(self, 1)
            # log('all solid')
            return
        elif max_ <= min_height:
            self._children[indices[0]] = OctreeLeaf(self, 0)
            self._children[indices[1]] = OctreeLeaf(self, 0)
            # log('all empty')
            return

        # handle top
        #
        if max_ <= origin:
            self._children[indices[0]] = OctreeLeaf(self, 0)
            # log('top empty')
        elif all_leaf:
            self._children[indices[0]] = OctreeLeaf(self, 1)
            # log('top solid')
        else:
            # log('top split')
            self._children[indices[0]] = OctreeInterior(self)
            self._children[indices[0]]._init_from_height_map(values, self._copy_data(data))

        # handle bottom
        #
        if min_ > origin or all_leaf:
            self._children[indices[1]] = OctreeLeaf(self, 1)
            # log('bottom solid')
        else:
            # log('bottom split')
            self._children[indices[1]] = OctreeInterior(self)
            self._children[indices[1]]._init_from_height_map(values, self._copy_data(data))

    def _init_from_height_map(self, values, data):
        # gather data to initialize each column individually
        #
        self._children = [None] * 8
        self._update_data(data)
        full_size = len(values)
        size = full_size / 2
        origin = data['origin'].y
        min_height = origin - (data['size']/2)
        max_height = origin + (data['size']/2)

        """
        x o
        o o
        """
        v = values[:size, :size]
        indices = (2, 0) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, data)

        """
        o x
        o o
        """
        v = values[size:full_size, :size]
        indices = (6, 4) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, data)

        """
        o o
        x o
        """
        v = values[:size, size:full_size]
        indices = (3, 1) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, data)

        """
        o o
        o x
        """
        v = values[size:full_size, size:full_size]
        indices = (7, 5) # top bottom
        self._init_column_from_height_map(v, indices, min_height, max_height, origin, data)

class AbstractOctreeChild(AbstractOctree):
    def parent(self):
        return self._parent

    def origin(self):
        data = self._get_data()
        return data['origin']

    def _add_point(self, point, point_data, data):
        copied_data = self._copy_data(data)
        self._update_data(copied_data)
        if point == copied_data['origin']:
            self.set_data(point_data)
            return self

        new_self = self.parent()._split_leaf(self)
        return new_self._add_point(point, point_data, data)

    def _update_data(self, data):
        data['level'] += 1
        data['size'] *= 0.5

        offset = self._offset()
        offset *= data['size']
        data['origin'] += offset

    def _get_data(self):
        data = self.parent()._get_data()
        self._update_data(data)
        return data

    def _offset(self):
        i = self.index()
        offset = Vector()
        offset.x = 0.5 if i&4 else -0.5
        offset.y = 0.5 if i&2 else -0.5
        offset.z = 0.5 if i&1 else -0.5
        return offset

    def index(self):
        return self._parent._children.index(self)

    def _render(self, game, shader, data):
        self._update_data(data)
        self._do_render(game, shader, data)

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

    def _merge(self):
        return self

    def _get_data(self):
        data = {}
        self._update_data(data)
        return data

    def _update_data(self, data):
        data['top'] = self
        data['level'] = 1
        data['size'] = self.size()
        data['origin'] = self.origin()

    def origin(self):
        return Point()

    def size(self):
        return self._size

    def add_point(self, point, point_data):
        return self._add_point(Point(point), point_data, {})

    def render(self, game, shader):
        data = self._get_data()
        self._do_render(game, shader, data)

    def generate_mesh(self):
        from ..data import cube
        from . import Mesh
        data = self._get_data()
        data['cube'] = cube
        data['index_offset'] = 0
        verts, normals, indices = self._generate_mesh(data)
        return Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def initialize_from_height_map(self, values):
        values = values[:-1, :-1]
        self._init_from_height_map(values, {})

    def get_height(self, x, z):
        return self._get_height(x,z,{})

class OctreeInterior(AbstractOctreeParent, AbstractOctreeChild):
    def __init__(self, parent):
        self._parent = parent
        # self._children = tuple([OctreeLeaf(self) for i in xrange(8)])

    @classmethod
    def from_leaf(cls, leaf):
        self = cls(leaf.parent())
        return self

class OctreeLeaf(AbstractOctreeChild):
    def __init__(self, parent, data=None):
        self._parent = parent
        self._data = data

    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data
        # TODO: possibly merge here

    def _get_height(self, x, z, data):
        if not self.data():
            return None
        self._update_data(data)
        return data['origin'].y+0.5

    def _is_leaf(self):
        return True

    def _do_render(self, game, shader, data):
        if self._data is None:
            return

        matrix = Matrix()
        matrix.translate(data['origin'])
        matrix.scale(data['size'])
        GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, matrix.tolist())

        # r = random.random()
        # g = random.random()
        # b = random.random()
        # GL.glUniform4f(shader.uniforms['diffuseColor'], r, g, b, 1.0)

        # print 'Drawing leaf:'
        # print '\t level:', data['level']
        # print '\t origin:', data['origin']
        # print '\t size:', data['size']
        # print '\t color: %f %f %f' % (r,g,b)
        # print '\t matrix:'
        # print matrix

        game.cube.render()

    def _generate_mesh(self, data):
        if not self.data():
            return
        self._update_data(data)

        VERTS = data['cube'].VERTICES
        verts = []
        origin = data['origin']
        size = data['size']
        for i in xrange(0, len(VERTS), 3):
            # vert = origin + Vector([VERTS[i], VERTS[i+1], VERTS[i+2]]) * size
            # verts.append(vert.x)
            # verts.append(vert.y)
            # verts.append(vert.z)
            verts.append(origin.x + VERTS[i] * size)
            verts.append(origin.y + VERTS[i+1] * size)
            verts.append(origin.z + VERTS[i+2] * size)
        normals = data['cube'].NORMALS
        indices = [i + data['index_offset'] for i in data['cube'].INDICES]
        return verts, normals, indices


