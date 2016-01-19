import random
from . import quadtree
from . import Point

class _HeightMapBranch(quadtree._QuadTreeBranch):
    def __init__(self, data):
        self._data = data
        super(_HeightMapBranch, self).__init__()
        self._children = self._children
        """:type: list[None|`_HeightMapBranch`|`_HeightMapLeaf`]"""

    def _generate_node_height(self, info, point, child_info):
        assert self._children[ child_info['index'] ] is None

        # find the items on this level that are adjacent to the new child item
        #
        """
        Corner indices:
            +y  2 3
            -y  0 1
               -x +x
        """
        corner_points = [
            Point(*info['origin']),
            Point(*info['origin']),
            Point(*info['origin']),
            Point(*info['origin']),
        ]

        if child_info['index'] & self._TREE_CLS._BITWISE_NUMS[0]:
            """
            Child is in one of these spots:
                . x
                . x
            """
            corner_points[1].x += info['size']
            corner_points[3].x += info['size']
        else:
            """
            Child is in one of these spots:
                x .
                x .
            """
            corner_points[0].x -= info['size']
            corner_points[2].x -= info['size']

        if child_info['index'] & self._TREE_CLS._BITWISE_NUMS[1]:
            """
            Child is in one of these spots:
                x x
                . .
            """
            corner_points[2].y += info['size']
            corner_points[3].y += info['size']
        else:
            """
            Child is in one of these spots:
                . .
                x x
            """
            corner_points[0].y -= info['size']
            corner_points[1].y -= info['size']


        avg_parent_height = 0.0
        for corner_point in corner_points:
            if corner_point == info['origin']:
                corner_item = self
            else:
                corner_item = info['tree'].get_node(corner_point, max_depth=info['level'])[0]
                if corner_item is None:  # TODO: properly deal with edges
                    avg_parent_height += info['tree']._root._data
                    continue
            avg_parent_height += corner_item._data
        avg_parent_height /= float( len(corner_points) )

        rand = random.Random(info['seed'])
        rand.jumpahead( info['origin'].x )
        rand.jumpahead( info['origin'].y )
        rand.jumpahead( info['origin'].z )

        max_deviation = 1.0 / float(info['level']**2)
        return avg_parent_height + rand.uniform(-max_deviation, max_deviation)

    def generate_node(self, info, point, max_depth=None):
        if max_depth is not None and info['level'] >= max_depth:
            return self, info
        index = self.get_closest_child_index(info, point)
        child_info = self.get_child_info(info, index, copy=True)
        height = self._generate_node_height(info, point, child_info)
        if child_info['level'] >= info['tree'].max_depth():
            cls = self._TREE_CLS._LEAF_CLS
            self._children[index] = cls(height)
            return self._children[index], child_info
        else:
            cls = self._TREE_CLS._BRANCH_CLS
            self._children[index] = cls(height)
            return self._children[index].generate_node(child_info, point, max_depth)

    def get_points(self, info):
        points = []
        for i, child in enumerate(self._children):
            child_info = self.get_child_info(info, i, copy=True)
            if child:
                points.extend( child.get_points(child_info) )
            else:
                point = Point(child_info['origin'].x, self._data, child_info['origin'].y)
                points.append(point)
        return points

class _HeightMapLeaf(quadtree._QuadTreeLeaf):
    def get_points(self, info):
        return [Point(info['origin'].x, self._data, info['origin'].y)]

class HeightMap(quadtree.QuadTree):
    INDENT = 0
    def __init__(self, size, max_depth, seed, base_height=0.0):
        self._seed = seed
        self._base_height = base_height
        self._points = None
        super(HeightMap, self).__init__(size, max_depth)

    def _create_root(self):
        root = self._BRANCH_CLS( self._base_height )
        root._children = [self._BRANCH_CLS( self._base_height )] * 4
        return root

    def _get_info(self):
        info = super(HeightMap, self)._get_info()
        info['seed'] = self._seed
        info['random'] = random.Random(self._seed)
        return info

    def store_points(self):
        from OpenGL import GL
        from OpenGLContext.arrays import array
        from . import FLOAT_SIZE
        info = self._get_info()
        self._points = self._root.get_points(info)
        # self._data = [c for p in self._points for c in p]
        # self._data = array(self._points, 'f')

        self.vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.vao)

        vertexBufferObject = GL.glGenBuffers(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertexBufferObject)
        data = [c for p in self._points for c in p]
        array_type = (GL.GLfloat*len(data))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(data)*FLOAT_SIZE,
            array_type(*data),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

        GL.glBindVertexArray(0)

    def render(self):
        from OpenGL import GL
        GL.glBindVertexArray(self.vao)
        GL.glDrawArrays(GL.GL_POINTS, 0, len(self._points))
        GL.glBindVertexArray(0)

_HeightMapBranch._TREE_CLS = HeightMap
_HeightMapLeaf._TREE_CLS = HeightMap

HeightMap._BRANCH_CLS = _HeightMapBranch
HeightMap._LEAF_CLS = _HeightMapLeaf
