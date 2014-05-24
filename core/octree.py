__all__ = ['Octree']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy
import random

from . import Point
from . import Vector

#============================================================================#
#=================================================================== CLASS ==#
class AbstractOctree(object):
    def _is_leaf(self):
        return False

    def _update_data(self, data):
        data['level'] += 1
        data['size'] *= 0.5

class AbstractOctreeParent(AbstractOctree):
    def children(self):
        return self._children

    def _split_leaf(self, child):
        children = list(self.children())
        index = children.index(child)
        children.remove(child)
        new_child = OctreeInterior.from_leaf(child)
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

    def _add_point(self, point, point_data, data):
        origin = self._origin(data)
        child = self._child_containing_point(point, origin)
        child_origin = child._origin(data)
        if point == child_origin:
            result = child
            child.set_data(point_data)
        else:
            if child._is_leaf():
                child = self._split_leaf(child)
            result = child._add_point(point, point_data, data)

        do_merge = True
        for child in self._children:
            if child.data() != result.data():
                do_merge = False
                break
        if do_merge:
            return self.parent()._merge()
        else:
            return result

    def _do_render(self, shader, matrix_stack, data):
        for child in self._children:
            child._render(shader, matrix_stack, {})

class AbstractOctreeChild(AbstractOctree):
    def parent(self):
        return self._parent

    def origin(self):
        return self._origin({})

    def _offset(self):
        i = self.index()
        offset = Vector()
        offset.x = 0.5 if i&4 else -0.5
        offset.y = 0.5 if i&2 else -0.5
        offset.z = 0.5 if i&1 else -0.5
        return offset

    def _origin(self, data):
        parent_origin = self.parent()._origin(data)
        self._update_data(data)
        offset = self._offset()
        size = data['size']
        offset *= size
        return parent_origin + offset

    def index(self):
        return self._parent._children.index(self)

    def _render(self, shader, matrix_stack, data):
        self._update_data(data)
        with matrix_stack:
            offset = self._offset()
            matrix_stack.translate(offset)
            matrix_stack.scale(0.5)

            self._do_render(self, shader, matrix_stack, data)

class Octree(AbstractOctreeParent):
    def __init__(self, size):
        super(Octree, self).__init__()
        self._size = size
        self._children = tuple([OctreeLeaf(self) for i in xrange(8)])

    def _merge(self):
        return self

    def _update_data(self, data):
        data['top'] = self
        data['level'] = 1
        data['size'] = self.size()

    def _origin(self, data):
        origin = self.origin()
        self._update_data(data)
        return origin

    def origin(self):
        return Point()

    def size(self):
        return self._size

    def add_point(self, point, point_data):
        return self._add_point(Point(point), point_data, {})

    def render(self, shader, matrix_stack):
        self._do_render(shader, matrix_stack, {})

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

    def _is_leaf(self):
        return True

    def _do_render(self, shader, matrix_stack, data):
        r = random.randrange(1.0)
        g = random.randrange(1.0)
        b = random.randrange(1.0)
        GL.glUniform4f(shader.uniforms['diffuseColor'], r, g, b, 1.0)

        GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, matrix_stack.top().tolist())
        self.cube.render()

# class Octree(object):
#     def __init__(self, parent=None):
#         self._parent = parent

#     def parent(self):
#         return self._parent

#     def size(self):
#         if hasattr(self, '_size'):
#             return self._size
#         else:
#             return self.parent().size() * 0.5

#     def origin(self):
#         if hasattr(self, '_origin'):
#             return self._origin
#         else:
#             return self.parent().child_origin(self)

#     def add_point(self, point, origin=[0.0, 0.0, 0.0]):
#         if point == origin:
#             return self

#         self.split()
#         child = self.child_containing_point(point)
#         return child.add_point(point)

#     def child_origin(self, child, size=None):
#         if size is None:
#             size = self.size()
#         i = self._children.index(child)
#         x = size * (0.5 if i&4 else 0.5)
#         y = size * (0.5 if i&2 else 0.5)
#         z = size * (0.5 if i&1 else 0.5)

#     def child_containing_point(self, point, origin):
#         index = 0
#         if point.x >= origin.x: index |= 4
#         if point.y >= origin.y: index |= 2
#         if point.z >= origin.z: index |= 1

#         return self.child(index)

#     def child(self, index):
#         return self._children[index]

#     def split(self):
#         if self._children is None:
#             self._children = [Octree(self) for i in xrange(8)]

#     def is_leaf(self):
#         return self._children is None

#     def has_children(self):
#         return (self._children is not None)

#     def iter_children(self):
#         if self.has_children():
#             for child in self._children:
#                 yield child

#     def compress(self):
#         if self._children is None:
#             return
#         has_non_leaf = False
#         for child in self.iter_children():
#             child.compress()
#             if child.has_children():
#                 has_non_leaf = True

#         # TODO: update compress with block detection
#         if has_non_leaf:
#             return

#         self.clear()

#     def clear(self):
#         for child in self.iter_children():
#             child._parent = None
#         self._children = None

#     def render(self, shader, matrix_stack, size=None, origin=None):
#         with matrix_stack:
#             if origin is not None:
#                 matrix_stack.translate(origin)
#                 matrix_stack.scale(0.5)

#             if self.is_leaf():
#                 r = random.randrange(1.0)
#                 g = random.randrange(1.0)
#                 b = random.randrange(1.0)
#                 GL.glUniform4f(shader.uniforms['diffuseColor'], r, g, b, 1.0)

#                 GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, matrix_stack.top().tolist())
#                 self.cube.render()
#             else:
#                 half_size = size / 2.0
#                 for i, child in enumerate(self.iter_children()):
#                     x = half_size * (0.5 if i&4 else 0.5)
#                     y = half_size * (0.5 if i&2 else 0.5)
#                     z = half_size * (0.5 if i&1 else 0.5)
#                     child.render(shader, matrix_stack, half_size, [x,y,z])

