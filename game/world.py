#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import random
import time

import numpy
import glfw
import noise

from OpenGL import GL

from ..data import cube
from .. import core
from ..core import octree

from ..core.logger import *

#============================================================================#
#=============================================================== FUNCTIONS ==#
def clamp(v, min_, max_):
    return max(min(v, max_), min_)

def fractal_rand():
    return (random.random() * 2.0) - 1.0

def avg_vals(i, j, values):
    return (values[i-1][j-1] + 
            values[i-1][j] +
            values[i][j-1] +
            values[i][j]) * 0.25

def avg_square_vals(i, j, stride, values):
    return (values[i-stride][j-stride] + 
            values[i-stride][j+stride] +
            values[i+stride][j-stride] +
            values[i+stride][j+stride]) * 0.25

def avg_diamond_vals(i, j, stride, size, values):
    if i == 0:
        return (values[i][j-stride] +
                values[i][j+stride] +
                values[size-stride][j] +
                values[i+stride][j]) * 0.25
    elif i == size:
        return (values[i][j-stride] +
                values[i][j+stride] +
                values[i-stride][j] +
                values[stride][j]) * 0.25
    elif j == 0:
        return (values[i-stride][j] +
                values[i+stride][j] +
                values[i][j+stride] +
                values[i][size-stride]) * 0.25
    elif j == size:
        return (values[i-stride][j] +
                values[i+stride][j] +
                values[i][j-stride] +
                values[i][stride]) * 0.25
    else:
        return (values[i-stride][j] +
                values[i+stride][j] +
                values[i][j-stride] +
                values[i][j+stride]) * 0.25

#============================================================================#
#=================================================================== CLASS ==#
class AbstractWorldOctreeBase(octree.AbstractOctreeBase):
    @property
    def _leaf_cls(self):
        return WorldOctreeLeaf

    @property
    def _interior_cls(self):
        return WorldOctreeInterior

    def _get_bbox(self, info):
        half_size = info['size'] * 0.5
        offset = core.Vector([half_size]*3)
        min_ = info['origin'] - offset
        max_ = info['origin'] + offset
        return core.BoundingBox(min_, max_)

class WorldOctreeInterior(octree.OctreeInterior, AbstractWorldOctreeBase):
    # def _render(self, game, shader, info):
    #     for child, child_info in self.iter_children_info(info):
    #         if info['size'] > 4:
    #             if abs(child_info['origin'][0]) > abs(info['origin'][0]):
    #                 continue
    #             # if abs(child_info['origin'][1]) > abs(info['origin'][1]):
    #             #     continue
    #             if abs(child_info['origin'][2]) > abs(info['origin'][2]):
    #                 continue
    #         child._render(game, shader, child_info)

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
            self._children[indices[0]] = self._leaf_cls(1)
            self._children[indices[1]] = self._leaf_cls(1)
            return
        elif max_ <= min_height:
            self._children[indices[0]] = self._leaf_cls(0)
            self._children[indices[1]] = self._leaf_cls(0)
            return

        # handle top
        #
        if max_ <= origin:
            self._children[indices[0]] = self._leaf_cls(0)
        elif all_leaf:
            self._children[indices[0]] = self._leaf_cls(1)
        else:
            self._children[indices[0]] = self._interior_cls()
            self._children[indices[0]]._init_from_height_map(values, self._get_child_info(info, indices[0]))

        # handle bottom
        #
        if min_ > origin or all_leaf:
            self._children[indices[1]] = self._leaf_cls(1)
        else:
            self._children[indices[1]] = self._interior_cls()
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

    def _get_collisions(self, bbox, info):
        this_bbox = self._get_bbox(info)
        collision = this_bbox.intersection(bbox)
        result = []
        if collision:
            for child, child_info in self.iter_children_info(info):
                child_collisions = child._get_collisions(bbox, child_info)
                result.extend(child_collisions)
        return result

class WorldOctreeLeaf(octree.OctreeLeaf, AbstractWorldOctreeBase):
    # def _render(self, game, shader, info):
    #     if not self.data():
    #         return

    #     # if abs(info['origin'][0]) > 5:
    #     #     return
    #     # if abs(info['origin'][2]) > 5:
    #     #     return
    #     if info['origin'][1] > 18 or info['origin'][1] < 10:
    #         return
    #     # if info['origin'][1] != 13.5:
    #     #     return

    #     mat = core.Matrix()
    #     mat[0,0] = mat[1,1] = mat[2,2] = info['size']
    #     mat[3,0] = info['origin'][0]
    #     mat[3,1] = info['origin'][1]
    #     mat[3,2] = info['origin'][2]

    #     # if game.do_printing:
    #     #     print 'rendering debug cube:'
    #     #     print mat

    #     GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat.tolist())
    #     game.cube.render()

    def _get_height(self, x, z, info):
        if not self.data():
            return None
        return info['origin'].y+(info['size'] / 2.0)

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
            # vert = origin + core.Vector([VERTS[i], VERTS[i+1], VERTS[i+2]]) * size
            # verts.append(vert.x)
            # verts.append(vert.y)
            # verts.append(vert.z)
            verts.append(origin.x + VERTS[i] * size)
            verts.append(origin.y + VERTS[i+1] * size)
            verts.append(origin.z + VERTS[i+2] * size)
        normals = info['cube'].NORMALS
        indices = [i + info['index_offset'] for i in info['cube'].INDICES]
        return verts, normals, indices

    def _get_collisions(self, bbox, info):
        if not bool(self.data()):
            return []
        this_bbox = self._get_bbox(info)
        collision = this_bbox.intersection(bbox)
        if collision:
            return [(collision, this_bbox)]
        else:
            return []

class World(octree.Octree, WorldOctreeInterior):
    def __init__(self, size):
        super(World, self).__init__(size)
        self.mesh = None

        stime = time.time()
        height_map = self._generate_height_map()
        print 'height map generation time:', (time.time() - stime)

        stime = time.time()
        self._init_from_height_map(height_map)
        print 'octree initialization time:', (time.time() - stime)

        # stime = time.time()
        # self._debug_mesh = None
        # self._generate_debug_mesh(height_map)
        # print 'debugging time:', (time.time() - stime)

        stime = time.time()
        self._generate_mesh()
        print 'mesh generation time:', (time.time() - stime)

    def _generate_height_map(self):
        """generates a height map using the diamond-square algorithm
        """

        size = int(self.size())
        values = numpy.zeros((size+1, size+1), dtype=float)
        sea_level = 0.0
        ratio = 0.5
        scale = float(size) / 8.0
        stride = size / 2

        random.seed(1234)
        while stride:
            # perform 'square' step
            #
            for i in xrange(stride, size, stride*2):
                for j in xrange(stride, size, stride*2):
                    values[i][j] = scale * fractal_rand() + avg_square_vals(i, j, stride, values)

            # perform 'diamond' step
            #
            oddline = False
            for i in xrange(0, size, stride):
                oddline = (oddline is False)
                start = 0
                if oddline:
                    start = stride
                for j in xrange(start, size, stride*2):
                    values[i][j] = scale * fractal_rand() + avg_diamond_vals(i, j, stride, size, values)

                    if i == 0:
                        values[size][j] = values[i][j]
                    if j == 0:
                        values[i][size] = values[i][j]

            scale *= ratio
            stride >>= 1

        values = values[:-1, :-1]
        return values

    def _generate_debug_mesh(self, values):
        # # print height map
        # #
        # start_x = -(self.size() / 2)
        # start_z = -(self.size() / 2)
        # for x, row in enumerate(values[:-1]):
        #     x = start_x + float(x) + 0.5
        #     for z, y in enumerate(row[:-1]):
        #         z = start_z + float(z) + 0.5
        #         top = self.get_height(x,z)
        #         bottom = top - 1.0
        #         if y > top or y <= bottom:
        #             print '(%s, %s): y=%f, top=%s, bottom=%s' % (x,z,y,top,bottom)

        # create a debug mesh that represents the heightmap
        #
        index_offset = 0
        verts = []
        normals = []
        indices = []
        start_x = -(self.size() / 2)
        start_z = -(self.size() / 2)
        for x, row in enumerate(values):
            x = start_x + float(x) + 0.5
            # if abs(x) > 8:
            #     continue
            for z, y in enumerate(row):
                z = start_z + float(z) + 0.5
                # if abs(z) > 8:
                #     continue

                # VERTS = cube.VERTICES
                # for i in xrange(12, 24, 3):
                #     verts.append(x+VERTS[i])
                #     verts.append(y+VERTS[i+1])
                #     verts.append(z+VERTS[i+2])
                # normals += cube.NORMALS[12:24]
                # faces = [0,1,3,2,3,1]
                # indices += [i + index_offset for i in faces]
                # index_offset += 4

                VERTS = cube.VERTICES
                for i in xrange(0, len(VERTS), 3):
                    verts.append(x+VERTS[i])
                    verts.append(y+VERTS[i+1])
                    verts.append(z+VERTS[i+2])
                normals += cube.NORMALS
                indices += [i + index_offset for i in cube.INDICES]
                index_offset += len(VERTS)/3

        self._debug_mesh = core.Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def _generate_mesh(self):
        info = self._get_info()
        info['cube'] = cube
        info['index_offset'] = 0
        verts, normals, indices = super(World, self)._generate_mesh(info)
        self.mesh = core.Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def _init_from_height_map(self, values):
        super(World, self)._init_from_height_map(values, self._get_info())

    def render(self, game):
        with game.shaders['skin'] as shader:
            GL.glUniformMatrix4fv(
                    shader.uniforms['modelToWorldMatrix'], 
                    1, 
                    GL.GL_FALSE, 
                    core.Matrix().tolist())
            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 1.0, 0.5, 1.0)
            self.mesh.render()

            # # render the debug mesh
            # #
            # GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
            # self._debug_mesh.render()

            # # render leaves individually for debugging
            # #
            # GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
            # info = self._get_info()
            # for child, child_info in self.iter_children_info(info):
            #     child._render(game, shader, child_info)

    def get_height(self, x, z):
        return self._get_height(x,z,self._get_info())

    def get_collisions(self, bbox):
        return self._get_collisions(bbox, self._get_info())

