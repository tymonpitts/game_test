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

#============================================================================#
#=================================================================== CLASS ==#
class AbstractOctree(object):
    def _is_leaf(self):
        return False

    def _copy_data(self, data):
        copied_data = {}
        copied_data['top'] = data['top']
        copied_data['level'] = data['level']
        copied_data['size'] = data['size']
        copied_data['origin'] = data['origin'].copy()
        return copied_data

    def data(self):
        return None

class AbstractOctreeParent(AbstractOctree):
    def data(self):
        return None

    def children(self):
        return self._children

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

class OctreeInterior(AbstractOctreeParent, AbstractOctreeChild):
    def __init__(self, parent):
        self._parent = parent
        self._children = tuple([OctreeLeaf(self) for i in xrange(8)])

    @classmethod
    def from_leaf(cls, leaf):
        self = cls(leaf.parent())
        return self

class OctreeLeaf(AbstractOctreeChild):
    def __init__(self, parent):
        self._parent = parent
        self._data = None

    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data
        # TODO: possibly merge here

    def _is_leaf(self):
        return True

    def _do_render(self, game, shader, data):
        matrix = Matrix()
        matrix.translate(data['origin'])
        matrix.scale(data['size'])
        GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, matrix.tolist())

        r = random.random()
        g = random.random()
        b = random.random()
        GL.glUniform4f(shader.uniforms['diffuseColor'], r, g, b, 1.0)
        # print 'Drawing leaf:'
        # print '\t level:', data['level']
        # print '\t origin:', data['origin']
        # print '\t size:', data['size']
        # print '\t color: %f %f %f' % (r,g,b)
        # print '\t matrix:'
        # print matrix

        game.cube.render()

