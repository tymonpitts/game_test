import random

from typing import List

from . import decorators
from . import abstract_tree
from . import quadtree
from . import Point
from . import BoundingBox2D


# TODO: update after AbstractTree refactor


class HeightMapNode(abstract_tree.TreeNode):

    @decorators.cached_method
    def get_bbox(self):
        """ Get the bounding box of this node

        The result of this function will be cached so subsequent calls will be faster.

        :rtype: BoundingBox2D
        """
        half_size = self.get_size() / 2.0
        half_size_point = Point(half_size, half_size)
        bbox_min = self.get_origin() - half_size_point
        bbox_max = self.get_origin() + half_size_point
        return BoundingBox2D(bbox_min, bbox_max)

    def _generate_debug_texture(self, viewport, width, height, texture):
        """
        Args:
            viewport (BoundingBox2D): viewport BoudingBox in actual heightmap coordinates (not pixels)
            width (int): viewport width in pixels
            height (int): viewport height in pixels
            data (List[float]): A flat list of color values that will be
                mutated with the height colors for each pixel.  The length of
                the list will be (width x height x 3).
        """
        # data range: -max_height to max_height
        max_height = self.tree.max_height
        height = self.get_value()
        if height is None:
            height = self.parent.get_value()
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
        # TODO: update viewport._min/_max references once BoundingBox2D class has been refactored
        relative_bottom_left = (origin - Point(half_size, half_size)) - viewport._min

        # account for partially obscured nodes
        #
        sizes = [self.get_size(), self.get_size()]
        relative_max = viewport._max + viewport._max
        for i in xrange(2):
            if relative_bottom_left[i] < 0.0:
                sizes[i] += relative_bottom_left[i]
                relative_bottom_left[i] = 0.0
            if (relative_bottom_left[i] + sizes[i]) > relative_max[i]:
                sizes[i] -= relative_bottom_left[i] + sizes[i] - relative_max[i]
        pixel_sizes = [int(s / min_size) for s in sizes]

        start_index = (int(relative_bottom_left.y / min_size) * width) + int(relative_bottom_left.x / min_size)
        for row in xrange(pixel_sizes[1]):
            index = start_index + (row * width)
            index *= 3
            for column in xrange(pixel_sizes[0]):
                column *= 3
                texture[index+column] = r
                texture[index+column+1] = g
                texture[index+column+2] = b

        # texture_index = (int(relative_bottom_left.y / min_size) * width) + int(relative_bottom_left.x / min_size)
        # texture_index *= 3
        # texture[texture_index] = r
        # texture[texture_index + 1] = g
        # texture[texture_index + 2] = b

    # def _generate_debug_mesh(self):
    #     if None in self._children:
    #         x = info['origin'].x
    #         z = info['origin'].y
    #         bottom = info['tree'].size() / -2.0
    #         size = info['size']
    #         normals = info['cube'].NORMALS
    #         cube_verts = info['cube'].VERTICES
    #         verts = []
    #         for i in xrange(0, len(cube_verts), 3):
    #             verts.append(x + cube_verts[i] * size)
    #             if cube_verts[i + 1] < 0.0:
    #                 verts.append(bottom)
    #             else:
    #                 verts.append(self._data)
    #             verts.append(z + cube_verts[i + 2] * size)
    #
    #         indices = [i + info['index_offset'] for i in info['cube'].INDICES]
    #         return verts, normals, indices
    #
    #     verts = []
    #     normals = []
    #     indices = []
    #     for child, child_info in self.iter_children_info(info):
    #         c_verts, c_normals, c_indices = child._generate_debug_mesh(child_info)
    #         info['index_offset'] += len(c_verts) / 3
    #         verts.extend(c_verts)
    #         normals.extend(c_normals)
    #         indices.extend(c_indices)
    #     return verts, normals, indices

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
        half_parent_size = parent_size / 2.0
        parent_origin = self.parent.get_origin()
        corner_points = [
            Point(*parent_origin),
            Point(*parent_origin),
            Point(*parent_origin),
            Point(*parent_origin),
        ]
        corner_weights = [
            1.0,
            1.0,
            1.0,
            1.0,
        ]

        if self.index & self.tree.dimension_bits[0]:
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
                new_x = -half_tree_size + half_parent_size
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
            if corner_points[0].x <= -half_tree_size:  # wrap to other side
                new_x = half_tree_size - half_parent_size
                corner_points[0].x = new_x
                corner_points[2].x = new_x

        if self.index & self.tree.dimension_bits[1]:
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
                new_y = -half_tree_size + half_parent_size
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
            if corner_points[0].y <= -half_tree_size:  # wrap to other side
                new_y = half_tree_size - half_parent_size
                corner_points[0].y = new_y
                corner_points[1].y = new_y

        # TODO: weighted average is producing horizontal and vertical lines in height
        parent_height = 0.0
        for i, corner_point in enumerate(corner_points):
            if corner_point == parent_origin:
                corner_node = self.parent
            else:
                # TODO: this node retrieval could likely be optimized by
                #       caching the parent level nodes by origin before
                #       generating child nodes
                corner_node = self.tree.get_node_from_point(corner_point, max_depth=self.parent.get_depth())
            corner_height = corner_node.get_value()
            parent_height += corner_height * corner_weights[i]
        parent_height /= sum(corner_weights)  # TODO: this could likely be optimized

        origin = self.get_origin()
        # TODO: optimize this to not rely on jumpahead since it is expensive
        rand = random.Random( self.tree.seed )
        rand.jumpahead( (origin.x, origin.y) )  # jumpahead is expensive so only doing it once for both x and y

        # max_deviation = 1.0 / float( (self.get_depth() + 1) ** 2 )
        # max_deviation = self.tree.get_size() / 2 ** ( self.get_depth() + 1 )
        max_deviation = self.tree.max_height / 2 ** ( float( self.get_depth() ) ** 0.92 )
        deviation = rand.uniform(-max_deviation, max_deviation)
        height = parent_height + deviation
        self.set_value(height)

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
        :rtype: HeightMapNode
        """
        return HeightMapNode(data, tree=self, parent=parent, index=index)

    def generate(self, point, max_depth=None):
        """Generates nodes centered around `point`.

        Falloff is based on size*depth

        :type point: Point
        :type max_depth: int
        """
        nodes = [self._create_node_proxy(self._data)]
        depth = 0
        size = self.size
        new_branch_data = [None] * (self.num_children + 1)
        max_depth = max_depth if max_depth is not None else self.max_depth
        while nodes and depth < max_depth:
            next_nodes = []
            """:type: list[HeightMapNode]"""
            max_distance = size * (depth + 1)
            for node in nodes:
                distance = point.distance( node.get_origin() )
                if distance <= max_distance:
                    if node.get_children() is None:
                        # TODO: flush `get_children` cache
                        # TODO: update the line below to set children after refactoring tree data storage
                        node._set_data( list(new_branch_data) )
                        node._generate_height()
                    next_nodes.extend( node.get_children() )
                # TODO: maybe unload children in an else statement here?
            nodes = next_nodes
            depth += 1
            size /= 2.0

    def generate_area(self, bbox):
        """Generates all nodes within the provided `bbox`.

        :type bbox: BoundingBox2D
        """
        nodes = [self._create_node_proxy(self._data)]
        depth = 0
        size = self.size
        new_branch_data = [None] * (self.num_children + 1)
        while nodes:
            next_nodes = []
            """:type: list[HeightMapNode]"""
            half_size = size / 2.0
            half_size_point = Point(half_size, half_size)
            for node in nodes:
                bbox_min = node.get_origin() - half_size_point
                bbox_max = node.get_origin() + half_size_point
                node_bbox = BoundingBox2D(bbox_min, bbox_max)
                if bbox.collides(node_bbox):
                    if node._data is None:
                        # TODO: flush `get_children` cache
                        # TODO: update the line below to set children after refactoring tree data storage
                        node._set_data( list(new_branch_data) )
                        node._generate_height()
                    next_nodes.extend( node.get_children() )
                # TODO: maybe unload children in an else statement here?
            nodes = next_nodes
            depth += 1
            size /= 2.0

    def generate_all(self):
        nodes = [self._create_node_proxy(self._data)]
        while nodes:
            next_nodes = []
            """:type: list[HeightMapNode]"""
            for node in nodes:
                if node._data is None:
                    node._generate_height()
                next_nodes.extend( node.get_children() )
            nodes = next_nodes

    def _generate_debug_texture(self, viewport, width, height, texture):
        """
        Args:
            viewport (BoundingBox2D): viewport BoudingBox in actual heightmap coordinates (not pixels)
            width (int): viewport width in pixels
            height (int): viewport height in pixels
            data (List[float]): A flat list of color values that will be
                mutated with the height colors for each pixel.  The length of
                the list will be (width x height x 3).
        """
        nodes = [self._create_node_proxy(self._root)]
        half_size = self.size / 2.0
        half_size_point = Point(half_size, half_size)
        while nodes:
            next_nodes = []  # type: List[HeightMapNode]
            for node in nodes:
                bbox = BoundingBox2D(node.get_origin() - half_size_point, node.get_origin() + half_size_point)
                if not viewport.collides(bbox):
                    continue
                if node.is_branch():
                    next_nodes.extend( node.get_children() )
                else:
                    node._generate_debug_texture(viewport, width, height, texture)
            nodes = next_nodes
            half_size /= 2.0

    # def _generate_debug_mesh(self):
    #     nodes = [self._create_node_proxy(self._root)]
    #     while nodes:
    #         next_nodes = []
    #         """:type: list[HeightMapNode]"""
    #         for node in nodes:
    #             if node._data is None:
    #                 node.parent._generate_debug_mesh()
    #             elif node.is_branch():
    #                 next_nodes.extend( node.get_children() )
    #             else:
    #                 node._generate_debug_mesh()
    #     #
    #     # if None in self._children:
    #     #     x = info['origin'].x
    #     #     z = info['origin'].y
    #     #     bottom = info['tree'].size() / -2.0
    #     #     size = info['size']
    #     #     normals = info['cube'].NORMALS
    #     #     cube_verts = info['cube'].VERTICES
    #     #     verts = []
    #     #     for i in xrange(0, len(cube_verts), 3):
    #     #         verts.append(x + cube_verts[i] * size)
    #     #         if cube_verts[i + 1] < 0.0:
    #     #             verts.append(bottom)
    #     #         else:
    #     #             verts.append(self._data)
    #     #         verts.append(z + cube_verts[i + 2] * size)
    #     #
    #     #     indices = [i + info['index_offset'] for i in info['cube'].INDICES]
    #     #     return verts, normals, indices
    #     #
    #     # verts = []
    #     # normals = []
    #     # indices = []
    #     # for child, child_info in self.iter_children_info(info):
    #     #     c_verts, c_normals, c_indices = child._generate_debug_mesh(child_info)
    #     #     info['index_offset'] += len(c_verts) / 3
    #     #     verts.extend(c_verts)
    #     #     normals.extend(c_normals)
    #     #     indices.extend(c_indices)
    #     # return verts, normals, indices

