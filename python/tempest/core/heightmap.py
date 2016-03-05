import random

import glfw

from . import quadtree
from . import Point
from . import BoundingBox2D

class _HeightMapNodeMixin(object):
    def _generate_debug_texture(self, info, viewport, width, height, texture):
        """
        :type info: dict
        :type viewport: `BoundingBox2D`
        :type width: int
        :type height: int
        :type texture: list[float]
        """
        # data range: -max_height to max_height
        max_height = info['tree']._max_height
        if self._data <= 0.0:
            r = g = (max_height+self._data) / max_height * 0.5
            b = 1.0
        elif self._data > max_height:
            r = g = b = 1.0
        else:
            r = self._data / max_height
            g = (max_height - self._data) / max_height
            b = 0.0

        # TODO: update viewport._min reference once BoundingBox2D class has been refactored
        half_size = self.get_size(info) / 2.0
        origin = self.get_origin(info)
        min_size = info['tree']._min_size
        relative_bottom_left = (origin - Point(half_size, half_size)) - viewport._min
        texture_index = (int(relative_bottom_left.y/min_size) * width) + int(relative_bottom_left.x/min_size)
        texture_index *= 3
        texture[texture_index] = r
        texture[texture_index+1] = g
        texture[texture_index+2] = b

class _HeightMapBranch(quadtree._QuadTreeBranch, _HeightMapNodeMixin):
    def __init__(self, data):
        self._data = data
        super(_HeightMapBranch, self).__init__()
        self._children = self._children
        """:type: list[None|`_HeightMapBranch`|`_HeightMapLeaf`]"""

    def _generate_node_height(self, info, point, child_index, origin):
        assert self._children[child_index] is None
        # if child_index == 0:
        #     return self._data

        # find the items on this level that are adjacent to the new child item
        #
        """
        Corner indices:
            +y  2 3
            -y  0 1
               -x +x
        """
        half_tree_size = info['tree']._size / 2.0
        size = self.get_size(info)
        child_size = size / 2.0
        corner_points = [
            Point(*origin),
            Point(*origin),
            Point(*origin),
            Point(*origin),
        ]
        corner_weights = [
            1.0,
            1.0,
            1.0,
            1.0,
        ]

        if child_index & self._TREE_CLS._BITWISE_NUMS[0]:
            """
            Child is in one of these spots:
                . x
                . x
            """
            corner_points[1].x += size
            corner_points[3].x += size
            corner_weights[1] += 1.0
            corner_weights[3] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[1].x >= half_tree_size:  # wrap to other side
                new_x = -half_tree_size + size
                corner_points[1].x = new_x
                corner_points[3].x = new_x
        else:
            """
            Child is in one of these spots:
                x .
                x .
            """
            corner_points[0].x -= size
            corner_points[2].x -= size
            corner_weights[0] += 1.0
            corner_weights[2] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[0].x < -half_tree_size:  # wrap to other side
                new_x = half_tree_size - size
                corner_points[0].x = new_x
                corner_points[2].x = new_x

        if child_info['index'] & self._TREE_CLS._BITWISE_NUMS[1]:
            """
            Child is in one of these spots:
                x x
                . .
            """
            corner_points[2].y += size
            corner_points[3].y += size
            corner_weights[2] += 1.0
            corner_weights[3] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[2].y >= half_tree_size:  # wrap to other side
                new_y = -half_tree_size + size
                corner_points[2].y = new_y
                corner_points[3].y = new_y
        else:
            """
            Child is in one of these spots:
                . .
                x x
            """
            corner_points[0].y -= size
            corner_points[1].y -= size
            corner_weights[0] += 1.0
            corner_weights[1] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[0].y < -half_tree_size:  # wrap to other side
                new_y = half_tree_size - size
                corner_points[0].y = new_y
                corner_points[1].y = new_y

        # TODO: weighted average is producing horizontal and vertical lines in height
        parent_height = 0.0
        for i, corner_point in enumerate(corner_points):
            if corner_point == origin:
                corner_item = self
            else:
                # this should always return a proper item
                depth = len(info['parents']) + 1
                corner_item = info['tree'].get_node(corner_point, max_depth=depth)[0]
            parent_height += corner_item._data * corner_weights[i]
        parent_height /= sum(corner_weights)

        child_origin = origin.copy()
        half_child_size = child_size * 0.5
        for i, num in enumerate(self._TREE_CLS._BITWISE_NUMS):
            if child_index & num:
                child_origin[i] += half_child_size
            else:
                child_origin[i] -= half_child_size

        rand = random.Random( info['seed'] )
        rand.jumpahead( (child_origin.x, child_origin.y) )  # jumpahead is expensive so only doing it once for both x and y

        # max_deviation = 1.0 / float(info['level']**2)
        # max_deviation = info['tree'].size() / 2**info['level']
        max_deviation = info['tree']._max_height / 2**( (len(info['parents'])+1)**0.92)
        deviation = rand.uniform(-max_deviation, max_deviation)
        return parent_height + deviation

    # TODO: should probably use child info here...
    def generate_node(self, info, point, max_depth=None):
        if max_depth is not None and len(info['parents']) >= max_depth:
            return self, info

        origin = self.get_origin(info)
        if origin.x == point.x and origin.y == point.y:
            return self, info

        child_index = self.get_closest_child_index(info, point)
        height = self._generate_node_height(info, point, child_index, origin)
        child_depth = len(info['parents']) + 1
        self.set_to_child_info(info, child_index)
        if child_depth >= info['tree']._max_depth:
            cls = self._TREE_CLS._LEAF_CLS
            self._children[index] = cls(height)
            return self._children[index], info
        else:
            cls = self._TREE_CLS._BRANCH_CLS
            self._children[index] = cls(height)
            return self._children[index].generate_node(info, point, max_depth)

    def get_points(self, info):
        points = []
        origin = self.get_origin(info)
        size = self.get_size(info)
        for child, child_info in self.iter_children_info(info):
            if child:
                points.extend( child.get_points(child_info) )
            else:
                child_origin = self.get_child_origin(child_info)
                point = Point(origin.x, self._data, origin.y)
                points.append(point)
        return points

    def generate(self, info, point):
        for child, child_info in self.iter_children_info(info):
            distance = point.distance( child_info['origin'] )
            max_distance = child_info['size'] * child_info['level']
            if distance <= max_distance:
                if child is None:
                    child, child_info = self.generate_node(info, child_info['origin'], max_depth=(child_info['level']-1), child_info=child_info)
                child.generate(child_info, point)
            # else:
            #     self._children[ child_info['index'] ] = None

    def generate_area(self, info, bbox):
        half_child_size = info['size'] / 4.0
        half_child_size_point = Point(half_child_size, half_child_size)
        for child, child_info in self.iter_children_info(info):
            child_bbox = BoundingBox2D(child_info['origin']-half_child_size_point, child_info['origin']+half_child_size_point)
            if bbox.collides(child_bbox):
                if child is None:
                    child, child_info = self.generate_node(info, child_info['origin'], max_depth=(child_info['level']-1), child_info=child_info)
                child.generate_area(child_info, bbox)
            else:
                self._children[ child_info['index'] ] = None

    def _generate_all_nodes(self, info, max_depth=None):
        if max_depth and info['level'] >= max_depth:
            return
        children = []
        for child, child_info in self.iter_children_info(info):
            if child is None:
                child = self.generate_node(info, child_info['origin'], child_info=child_info)[0]
            children.append( (child, child_info) )

        for child, child_info in children:
            child._generate_all_nodes(child_info, max_depth)

    def _generate_debug_mesh(self, info):
        if None in self._children:
            x = info['origin'].x
            z = info['origin'].y
            bottom = info['tree'].size() / -2.0
            size = info['size']
            normals = info['cube'].NORMALS
            cube_verts = info['cube'].VERTICES
            verts = []
            for i in xrange(0, len(cube_verts), 3):
                verts.append(x + cube_verts[i] * size)
                if cube_verts[i + 1] < 0.0:
                    verts.append(bottom)
                else:
                    verts.append(self._data)
                verts.append(z + cube_verts[i + 2] * size)

            indices = [i + info['index_offset'] for i in info['cube'].INDICES]
            return verts, normals, indices

        verts = []
        normals = []
        indices = []
        for child, child_info in self.iter_children_info(info):
            c_verts, c_normals, c_indices = child._generate_debug_mesh(child_info)
            info['index_offset'] += len(c_verts) / 3
            verts.extend(c_verts)
            normals.extend(c_normals)
            indices.extend(c_indices)
        return verts, normals, indices

    def __generate_debug_texture__leaf(self, info, child_info, viewport, width, height, texture):
        """
        :type info: dict
        :type child_info: dict
        :type viewport: `BoundingBox2D`
        :type width: int
        :type height: int
        :type texture: list[float]
        """
        # data range: -max_height to max_height
        max_height = child_info['tree']._max_height
        if self._data <= 0.0:
            r = g = (max_height+self._data) / max_height * 0.5
            b = 1.0
        elif self._data > max_height:
            r = g = b = 1.0
        else:
            r = self._data / max_height
            g = (max_height - self._data) / max_height
            b = 0.0

        half_size = child_info['size'] / 2.0
        relative_bottom_left = (child_info['origin'] - Point(half_size, half_size)) - viewport._min
        # size = int(child_info['size'] / child_info['min_size'])  # size in pixels

        # account for partially obscured nodes
        #
        sizes = [child_info['size'], child_info['size']]
        relative_max = viewport._max + viewport._max
        for i in xrange(2):
            if relative_bottom_left[i] < 0.0:
                sizes[i] += relative_bottom_left[i]
                relative_bottom_left[i] = 0.0
            if (relative_bottom_left[i]+sizes[i]) > relative_max[i]:
                sizes[i] -= relative_bottom_left[i] + sizes[i] - relative_max[i]
        pixel_sizes = [int(s / child_info['min_size']) for s in sizes]

        start_index = (int(relative_bottom_left.y/child_info['min_size']) * width) + int(relative_bottom_left.x/child_info['min_size'])
        for row in xrange(pixel_sizes[1]):
            index = start_index + (row * width)
            index *= 3
            for column in xrange(pixel_sizes[0]):
                column *= 3
                texture[index+column] = r
                texture[index+column+1] = g
                texture[index+column+2] = b

    def _generate_debug_texture(self, info, viewport, width, height, texture):
        """
        :type info: dict
        :param viewport: viewport BoudingBox in actual heightmap coordinates (not pixels)
        :type viewport: `BoundingBox2D`
        :param int width: viewport width in pixels
        :param int height: viewport height in pixels
        :type texture: list[float]
        """
        # TODO: this bbox stuff could probably be a little faster
        half_child_size = info['size'] / 4.0
        half_child_size_point = Point(half_child_size, half_child_size)
        for child, child_info in self.iter_children_info(info):
            child_bbox = BoundingBox2D(child_info['origin']-half_child_size_point, child_info['origin']+half_child_size_point)
            if not viewport.collides(child_bbox):
                continue
            try:
                child._generate_debug_texture(child_info, viewport, width, height, texture)
            except AttributeError:
                if child is not None:
                    raise
                self.__generate_debug_texture__leaf(info, child_info, viewport, width, height, texture)

class _HeightMapLeaf(quadtree._QuadTreeLeaf, _HeightMapNodeMixin):
    def generate(self, info, point):
        return

    def generate_area(self, info, bbox):
        return

    def get_points(self, info):
        return [Point(info['origin'].x, self._data, info['origin'].y)]

    def _generate_all_nodes(self, info, max_depth=None):
        return

    def _generate_debug_mesh(self, info):
        # generate mesh data for this point
        #
        x = info['origin'].x
        z = info['origin'].y
        bottom = info['tree'].size() / -2.0
        size = info['size']
        normals = info['cube'].NORMALS
        cube_verts = info['cube'].VERTICES
        verts = []
        for i in xrange(0, len(cube_verts), 3):
            verts.append(x + cube_verts[i] * size)
            if cube_verts[i + 1] < 0.0:
                verts.append(bottom)
            else:
                verts.append(self._data)
            verts.append(z + cube_verts[i + 2] * size)

        indices = [i + info['index_offset'] for i in info['cube'].INDICES]
        return verts, normals, indices

class HeightMap(quadtree.QuadTree):
    def __init__(self, size, max_height, max_depth, seed, base_height=0.0):
        self._seed = seed
        self._max_height = max_height
        self._base_height = base_height
        self._points = None
        super(HeightMap, self).__init__(size, max_depth)

    def generate(self, point):
        """Generates nodes centered around `point`.

        Falloff is based on size*depth

        :type point: `Point`
        """
        self._root.generate(self._get_info(), point)

    def generate_area(self, bbox):
        """Generates all nodes within the provided `bbox`.

        :type bbox: `BoundingBox2D`
        """
        self._root.generate_area(self._get_info(), bbox)

    def _create_root(self):
        root = self._BRANCH_CLS( self._base_height )
        root._children = [self._BRANCH_CLS( self._base_height ) for i in xrange(4)]
        return root

    def _get_info(self):
        info = super(HeightMap, self)._get_info()
        info['seed'] = self._seed
        return info

_HeightMapBranch._TREE_CLS = HeightMap
_HeightMapLeaf._TREE_CLS = HeightMap

HeightMap._BRANCH_CLS = _HeightMapBranch
HeightMap._LEAF_CLS = _HeightMapLeaf
