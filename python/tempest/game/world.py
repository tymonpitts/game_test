#============================================================================#
#================================================================= IMPORTS ==#
import random
import time

import numpy
from OpenGL import GL

from ..data import cube
from .. import core
from ..core import octree
from . import blocks
from . import GAME


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
class AbstractWorldOctreeBase(object):
    @staticmethod
    def _get_bbox(info):
        half_size = info['size'] * 0.5
        offset = core.Vector(half_size, half_size, half_size)
        min_ = info['origin'] - offset
        max_ = info['origin'] + offset
        return core.BoundingBox(min_, max_)

    def _get_height(self, info, x, z):
        raise NotImplementedError

    def _generate_mesh(self, info):
        raise NotImplementedError

    def _get_collisions(self, info, bbox):
        raise NotImplementedError

    def _get_blocks(self, info, bbox, exclude_types, inclusive):
        raise NotImplementedError
    
    def _get_block(self, info, point):
        raise NotImplementedError

    def _is_grounded(self, info, bbox):
        raise NotImplementedError


class _WorldOctreeBranch(AbstractWorldOctreeBase, octree._OctreeBranch):
    # def _render(self, info, shader):
    #     for child, child_info in self.iter_children_info(info):
    #         if info['size'] > 4:
    #             if abs(child_info['origin'][0]) > abs(info['origin'][0]):
    #                 continue
    #             # if abs(child_info['origin'][1]) > abs(info['origin'][1]):
    #             #     continue
    #             if abs(child_info['origin'][2]) > abs(info['origin'][2]):
    #                 continue
    #         child._render(child_info, shader)

    def _get_height(self, info, x, z):
        origin = info['origin']
        index1 = 0
        if x >= origin.x: index1 |= self._TREE_CLS._BITWISE_NUMS[0]
        if z >= origin.z: index1 |= self._TREE_CLS._BITWISE_NUMS[2]
        index2 = index1
        index1 |= self._TREE_CLS._BITWISE_NUMS[1]

        child1 = self._children[index1]
        height = child1._get_height(self._get_child_info(info, index1), x, z)
        if height is not None:
            return height

        child2 = self._children[index2]
        return child2._get_height(self._get_child_info(info, index2), x, z)

    def _get_child_info__debug(self, info, index, copy=True):
        top_node = info['parents'][0]

        if copy:
            stime = time.time()
            info = info.copy()
            top_node._mesh_times['get_child_info: copy'] += time.time() - stime
            stime = time.time()
            info['origin'] = info['origin'].copy()
            top_node._mesh_times['get_child_info: copy origin'] += time.time() - stime
            stime = time.time()
            info['parents'] = list(info['parents'])
            top_node._mesh_times['get_child_info: copy parents'] += time.time() - stime
        stime = time.time()
        info['level'] += 1
        info['size'] *= 0.5
        info['index'] = index
        info['parents'].append(self)
        top_node._mesh_times['get_child_info: misc'] += time.time() - stime

        stime = time.time()
        half_size = info['size'] * 0.5
        offset = []
        for i, num in enumerate(self._TREE_CLS._BITWISE_NUMS):
            offset.append( half_size if index&num else -half_size )

        top_node._mesh_times['get_child_info: get offset'] += time.time() - stime

        stime = time.time()
        for i, component in enumerate(offset):
            info['origin'][i] += component
        top_node._mesh_times['get_child_info: add offset'] += time.time() - stime

        return info

    def _generate_mesh(self, info):
        top_node = info['parents'][0]
        verts = []
        normals = []
        indices = []
        # for index, child in enumerate(self._children):
        #     child_info = self._get_child_info__debug(info, index)
        for child, child_info in self.iter_children_info(info):
            result = child._generate_mesh(child_info)
            if result is None:
                continue
            # stime = time.time()
            c_verts, c_normals, c_indices = result
            info['index_offset'] += len(c_verts)/3
            verts.extend(c_verts)
            normals.extend(c_normals)
            indices.extend(c_indices)
            # top_node._mesh_times['extending_arrays'] += time.time() - stime
        return verts, normals, indices

    def _init_column_from_height_map(self, info, values, indices, min_height, max_height, origin):
        max_ = values.max()
        min_ = values.min()
        all_leaf = (len(values) == 1)

        # handle cases where both children are either solid or empty
        #
        if min_ > max_height:
            self._children[indices[0]] = self._TREE_CLS._LEAF_CLS(1)
            self._children[indices[1]] = self._TREE_CLS._LEAF_CLS(1)
            return
        elif max_ <= min_height:
            self._children[indices[0]] = self._TREE_CLS._LEAF_CLS(0)
            self._children[indices[1]] = self._TREE_CLS._LEAF_CLS(0)
            return

        # handle top
        #
        if max_ <= origin:
            self._children[indices[0]] = self._TREE_CLS._LEAF_CLS(0)
        elif all_leaf:
            self._children[indices[0]] = self._TREE_CLS._LEAF_CLS(1)
        else:
            self._children[indices[0]] = self._TREE_CLS._BRANCH_CLS()
            self._children[indices[0]]._init_from_height_map(self._get_child_info(info, indices[0]), values)

        # handle bottom
        #
        if min_ > origin or all_leaf:
            self._children[indices[1]] = self._TREE_CLS._LEAF_CLS(1)
        else:
            self._children[indices[1]] = self._TREE_CLS._BRANCH_CLS()
            self._children[indices[1]]._init_from_height_map(self._get_child_info(info, indices[1]), values)

    def _init_from_height_map(self, info, values):
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
        indices = (2, 0) # -x -z
        self._init_column_from_height_map(info, v, indices, min_height, max_height, origin)

        """
        o x
        o o
        """
        v = values[size:full_size, :size]
        indices = (3, 1) # +x -z
        self._init_column_from_height_map(info, v, indices, min_height, max_height, origin)

        """
        o o
        x o
        """
        v = values[:size, size:full_size]
        indices = (6, 4) # -x +z
        self._init_column_from_height_map(info, v, indices, min_height, max_height, origin)

        """
        o o
        o x
        """
        v = values[size:full_size, size:full_size]
        indices = (7, 5) # +x +z
        self._init_column_from_height_map(info, v, indices, min_height, max_height, origin)

    def _get_collisions(self, info, bbox):
        this_bbox = self._get_bbox(info)
        collision = this_bbox.intersection(bbox)
        result = []
        if collision:
            for child, child_info in self.iter_children_info(info):
                child_collisions = child._get_collisions(child_info, bbox)
                result.extend(child_collisions)
        return result

    def _get_blocks(self, info, bbox, exclude_types, inclusive):
        this_bbox = self._get_bbox(info)
        collision = this_bbox.intersection(bbox, inclusive)
        results = []
        if collision:
            for child, child_info in self.iter_children_info(info):
                results.extend(child._get_blocks(child_info, bbox, exclude_types, inclusive))
        return results

    def _get_block(self, info, point):
        index = self._child_index_closest_to_point(info, point)
        child = self._children[index]
        child_info = self._get_child_info(info, index)
        return child._get_block(child_info, point)

    def _is_grounded(self, info, bbox):
        this_bbox = self._get_bbox(info)
        if this_bbox.collides(bbox, inclusive=[1]):
            for child, child_info in self.iter_children_info(info):
                if child._is_grounded(child_info, bbox):
                    return True
        return False


class _WorldOctreeLeaf(AbstractWorldOctreeBase, octree._OctreeLeaf):
    # def _render(self, info, shader):
    #     if not self._data:
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

    #     # if GAME.do_printing:
    #     #     print 'rendering debug cube:'
    #     #     print mat

    #     GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat.tolist())
    #     GAME.cube.render()

    def _get_height(self, info, x, z):
        if not self._data:
            return None
        return info['origin'].y+(info['size'] / 2.0)

    def _generate_mesh(self, info):
        top_node = info['parents'][0]
        # stime = time.time()
        block = self._get_block(info, None)
        # top_node._mesh_times['should_generate_mesh: get_block'] += time.time() - stime
        should_generate_mesh = block.should_generate_mesh()
        if not should_generate_mesh:
            return

        # generate mesh data for this point
        #
        # stime = time.time()
        origin_x = info['origin'].x
        origin_y = info['origin'].y
        origin_z = info['origin'].z
        size = info['size']
        normals = info['cube'].NORMALS
        cube_verts = info['cube'].VERTICES
        # top_node._mesh_times['gathering_info'] += time.time() - stime
        # stime = time.time()
        verts = []
        for i in xrange(0, len(cube_verts), 3):
            # vert = origin + core.Vector([cube_verts[i], cube_verts[i+1], cube_verts[i+2]]) * size
            # verts.append(vert.x)
            # verts.append(vert.y)
            # verts.append(vert.z)
            verts.append(origin_x + cube_verts[i] * size)
            verts.append(origin_y + cube_verts[i+1] * size)
            verts.append(origin_z + cube_verts[i+2] * size)
        # top_node._mesh_times['generating_verts'] += time.time() - stime

        # stime = time.time()
        indices = [i + info['index_offset'] for i in info['cube'].INDICES]
        # top_node._mesh_times['generating_indices'] += time.time() - stime
        return verts, normals, indices

    def _get_collisions(self, info, bbox):
        if not bool(self._data):
            return []
        this_bbox = self._get_bbox(info)
        collision = this_bbox.intersection(bbox)
        if collision:
            return [(collision, self._get_block(info, None))]
        else:
            return []

    def _get_blocks(self, info, bbox, exclude_types, inclusive):
        block_cls = GAME.get_block_cls(self._data)
        if block_cls in exclude_types:
            return []

        this_bbox = self._get_bbox(info)
        collision = this_bbox.intersection(bbox, inclusive)
        if collision:
            return [block_cls(GAME, self, info)]
        else:
            return []

    def _get_block(self, info, point):
        block_cls = GAME.get_block_cls(self._data)
        return block_cls(GAME, self, info)

    def _is_grounded(self, info, bbox):
        block_cls = GAME.get_block_cls(self._data)
        if not block_cls.is_solid():
            return False

        this_bbox = self._get_bbox(info)
        return this_bbox.collides(bbox, inclusive=[1])


class World(octree.Octree):
    def __init__(self, size):
        """
        :param int size:
        """
        super(World, self).__init__(size)
        self.mesh = None

        stime = time.time()
        self._generation_height_map = self._generate_height_map()
        print 'height map generation time:', (time.time() - stime)

        stime = time.time()
        self._init_from_height_map(self._generation_height_map)
        print 'octree initialization time:', (time.time() - stime)

        # stime = time.time()
        # self._debug_mesh = None
        # self._generate_debug_mesh(height_map)
        # print 'debugging time:', (time.time() - stime)

        stime = time.time()
        # self._mesh_times = OrderedDict()
        # self._mesh_times['get_child_info: copy'] = 0.0
        # self._mesh_times['get_child_info: copy origin'] = 0.0
        # self._mesh_times['get_child_info: copy parents'] = 0.0
        # self._mesh_times['get_child_info: misc'] = 0.0
        # self._mesh_times['get_child_info: get offset'] = 0.0
        # self._mesh_times['get_child_info: add offset'] = 0.0
        # self._mesh_times['should_generate_mesh: get_block'] = 0.0
        # self._mesh_times['should_generate_mesh: bbox'] = 0.0
        # self._mesh_times['should_generate_mesh: get_neighbors'] = 0.0
        # self._mesh_times['should_generate_mesh: neighbor_check'] = 0.0
        # self._mesh_times['gathering_info'] = 0.0
        # self._mesh_times['generating_verts'] = 0.0
        # self._mesh_times['generating_indices'] = 0.0
        # self._mesh_times['extending_arrays'] = 0.0
        # self._mesh_times['creating_mesh'] = 0.0
        self._generate_mesh()
        total_time = time.time() - stime
        # print 'mesh generation times:'
        # accounted_time = 0.0
        # for key, value in self._mesh_times.iteritems():
        #     print '  %s:' % key, value
        #     accounted_time += value

        # print '  unaccounted for:', (total_time - accounted_time)
        # print '  TOTAL:', total_time
        print 'mesh generation time:', total_time

    def _generate_height_map(self):
        """generates a height map using a modified diamond-square algorithm
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
            odd_line = False
            for i in xrange(0, size, stride):
                odd_line = (odd_line is False)
                start = 0
                if odd_line:
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

        # create a debug mesh that represents the height map
        #
        index_offset = 0
        verts = []
        normals = []
        indices = []
        start_x = -(self.size() / 2)
        start_z = -(self.size() / 2)
        cube_verts = cube.VERTICES
        for x, row in enumerate(values):
            x = start_x + float(x) + 0.5
            # if abs(x) > 8:
            #     continue
            for z, y in enumerate(row):
                z = start_z + float(z) + 0.5
                # if abs(z) > 8:
                #     continue

                # for i in xrange(12, 24, 3):
                #     verts.append(x+cube_verts[i])
                #     verts.append(y+cube_verts[i+1])
                #     verts.append(z+cube_verts[i+2])
                # normals += cube.NORMALS[12:24]
                # faces = [0,1,3,2,3,1]
                # indices += [i + index_offset for i in faces]
                # index_offset += 4

                for i in xrange(0, len(cube_verts), 3):
                    verts.append(x+cube_verts[i])
                    verts.append(y+cube_verts[i+1])
                    verts.append(z+cube_verts[i+2])
                normals += cube.NORMALS
                indices += [i + index_offset for i in cube.INDICES]
                index_offset += len(cube_verts)/3

        self._debug_mesh = core.Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def _generate_mesh(self):
        info = self._get_info()
        info['cube'] = cube
        info['index_offset'] = 0
        verts, normals, indices = self._root._generate_mesh(info)
        # stime = time.time()
        self.mesh = core.Mesh(verts, normals, indices, GL.GL_TRIANGLES)
        # self._mesh_times['creating_mesh'] = time.time() - stime

    def _init_from_height_map(self, values):
        self._root._init_from_height_map(self._get_info(), values)

    def render(self):
        with self.game.shaders['skin'] as shader:
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
            #     child._render(child_info, shader)

    def get_height(self, x, z):
        return self._root._get_height(self._get_info(), x, z)

    def get_collisions(self, bbox):
        return self._root._get_collisions(self._get_info(), bbox)

    def get_blocks(self, bbox, exclude_types=None, inclusive=None):
        """Retrieve a list of blocks contained within *bbox*

        :param bbox: The area to retrieve blocks from.
        :type bbox: :class:`.BoundingBox`
        :param exclude_types: A list of block types to exclude from the returned value. [default: [blocks.Air]]
        :type exclude_types: list of :class:`.AbstractBlock` types
        :param inclusive: Whether or not to include blocks that touch the edges of *bbox*.
            The elements in this list determine which components are inclusive.
        :type inclusive: list of int

        :rtype: list of :class:`.AbstractBlock` instances
        """
        if exclude_types is None:
            exclude_types = [blocks.Air]
        if inclusive is None:
            inclusive = []
        return self._root._get_blocks(self._get_info(), bbox, exclude_types, inclusive)

    def get_block(self, point):
        bounds = self.size() / 2.0
        if point.x > bounds or point.z > bounds or point.y > bounds:
            return None
        return self._root._get_block(self._get_info(), point)

    def is_grounded(self, bbox):
        return self._root._is_grounded(self._get_info(), bbox)


_WorldOctreeBranch._TREE_CLS = World
_WorldOctreeLeaf._TREE_CLS = World

World._LEAF_CLS = _WorldOctreeLeaf
World._BRANCH_CLS = _WorldOctreeBranch

