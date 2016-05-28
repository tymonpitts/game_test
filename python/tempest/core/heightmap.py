import random

from . import abstract_tree
from . import quadtree
from . import Point
from . import BoundingBox2D

class _HeightMapBranch(quadtree._QuadTreeBranch, _HeightMapNodeMixin):

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

class HeightMapNode(abstract_tree.TreeNode):
    def get_height(self):
        if self.is_branch():
            return self._data[4]
        else:
            return self._data

    def _generate_debug_texture(self, viewport, width, height, texture):
        """
        :type viewport: `BoundingBox2D`
        :type width: int
        :type height: int
        :type texture: list[float]
        """
        # data range: -max_height to max_height
        max_height = self.tree.max_height
        height = self.get_height()
        if height <= 0.0:
            r = g = (max_height + height) / max_height * 0.5
            b = 1.0
        elif height > max_height:
            r = g = b = 1.0
        else:
            r = height / max_height
            g = (max_height - height) / max_height
            b = 0.0

        half_size = self.get_size() / 2.0
        origin = self.get_origin()
        min_size = self.tree.min_size
        # TODO: update viewport._min reference once BoundingBox2D class has been refactored
        relative_bottom_left = (origin - Point(half_size, half_size)) - viewport._min
        texture_index = (int(relative_bottom_left.y / min_size) * width) + int(relative_bottom_left.x / min_size)
        texture_index *= 3
        texture[texture_index] = r
        texture[texture_index + 1] = g
        texture[texture_index + 2] = b

    def generate_data(self):
        height = self._generate_height()

    def _generate_height(self):
        # find the items at the parent depth that are adjacent to this node
        #
        """
        Corner indices:
            +y  2 3
            -y  0 1
               -x +x
        """
        half_tree_size = self.tree.size / 2.0
        parent_size = self.parent.get_size()
        size = parent_size / 2.0
        origin = self.parent.get_origin()
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

        if self.index & self.tree.BITWISE_NUMS[0]:
            """
            Child is in one of these spots:
                . x
                . x
            """
            corner_points[1].x += parent_size
            corner_points[3].x += parent_size
            corner_weights[1] += 1.0
            corner_weights[3] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[1].x >= half_tree_size:  # wrap to other side
                new_x = -half_tree_size + parent_size
                corner_points[1].x = new_x
                corner_points[3].x = new_x
        else:
            """
            Child is in one of these spots:
                x .
                x .
            """
            corner_points[0].x -= parent_size
            corner_points[2].x -= parent_size
            corner_weights[0] += 1.0
            corner_weights[2] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[0].x < -half_tree_size:  # wrap to other side
                new_x = half_tree_size - parent_size
                corner_points[0].x = new_x
                corner_points[2].x = new_x

        if child_info['index'] & self._TREE_CLS._BITWISE_NUMS[1]:
            """
            Child is in one of these spots:
                x x
                . .
            """
            corner_points[2].y += parent_size
            corner_points[3].y += parent_size
            corner_weights[2] += 1.0
            corner_weights[3] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[2].y >= half_tree_size:  # wrap to other side
                new_y = -half_tree_size + parent_size
                corner_points[2].y = new_y
                corner_points[3].y = new_y
        else:
            """
            Child is in one of these spots:
                . .
                x x
            """
            corner_points[0].y -= parent_size
            corner_points[1].y -= parent_size
            corner_weights[0] += 1.0
            corner_weights[1] += 1.0

            # TODO: change this once you implement world patches
            if corner_points[0].y < -half_tree_size:  # wrap to other side
                new_y = half_tree_size - parent_size
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
        half_child_size = size * 0.5
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

class HeightMap(quadtree.QuadTree):
    """

    Data format:

    - Branches: list with length 5.  First 4 items are children data, last item
        is the height of the branch node
    - Leaves: height of the node
    """
    def __init__(self, size, max_height, max_depth, seed, base_height=0.0):
        self.seed = seed
        self.max_height = max_height
        self.base_height = base_height
        super(HeightMap, self).__init__(size, max_depth)

    def _create_node_proxy(self, data, parent=None, index=0):
        """
        :rtype: TreeNode
        """
        return HeightMapNode(data, tree=self, parent=parent, index=index)

    def generate(self, point, max_depth=None):
        """Generates nodes centered around `point`.

        Falloff is based on size*depth

        :type point: `Point`
        """
        nodes = [self._create_node_proxy(self._root)]
        """:type: list[HeightMapNode]"""
        depth = 0
        size = self.size
        while nodes and (max_depth is None or depth <= max_depth):
            next_nodes = []
            """:type: list[HeightMapNode]"""
            max_distance = size * (depth + 1)
            for node in nodes:
                distance = point.distance( node.get_origin() )
                if distance <= max_distance:
                    if node._data is None:
                        node.generate_data()
                    next_nodes.extend( node.get_children() )
                # TODO: maybe unload children in an else statement here?
            nodes = next_nodes
            depth += 1
            size /= 2.0

    def generate_area(self, bbox):
        """Generates all nodes within the provided `bbox`.

        :type bbox: `BoundingBox2D`
        """
        self._root.generate_area(self._get_info(), bbox)

    def _create_root(self):
        root = super(HeightMap, self)._create_root()
        root.append(self.base_height)
        return root

_HeightMapBranch._TREE_CLS = HeightMap
_HeightMapLeaf._TREE_CLS = HeightMap

HeightMap._BRANCH_CLS = _HeightMapBranch
HeightMap._LEAF_CLS = _HeightMapLeaf
