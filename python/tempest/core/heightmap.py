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

        rand = random.Random( info['seed'] )
        rand.jumpahead( child_info['origin'].x )
        rand.jumpahead( child_info['origin'].y )

        max_deviation = 1.0 / float(info['level']**2)
        deviation = rand.gauss(0.0, max_deviation)
        return avg_parent_height + (deviation * info['tree']._max_height)

    def generate_node(self, info, point, max_depth=None, child_info=None):
        if max_depth is not None and info['level'] >= max_depth:
            return self, info
        if info['origin'].x == point.x and info['origin'].y == point.y:
            return self, info
        index = self.get_closest_child_index(info, point)
        child_info = child_info or self.get_child_info(info, index, copy=True)
        height = self._generate_node_height(info, point, child_info)
        if child_info['level'] >= info['tree'].max_depth():
            cls = self._TREE_CLS._LEAF_CLS
            self._children[index] = cls(height)
            return self._children[index], child_info
        else:
            cls = self._TREE_CLS._BRANCH_CLS
            self._children[index] = cls(height)
            return self._children[index].generate_node(child_info, point, max_depth)

    def generate_all_nodes(self, info, max_depth=None):
        if max_depth and info['level'] >= max_depth:
            return
        children = []
        for child, child_info in self.iter_children_info(info):
            if child is None:
                child = self.generate_node(info, child_info['origin'], child_info=child_info)[0]
            children.append( (child, child_info) )

        for child, child_info in children:
            child.generate_all_nodes(child_info, max_depth)

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

    def _generate_mesh(self, info):
        if None in self._children:
            x = info['origin'].x
            y = self._data
            z = info['origin'].y
            size = info['size']
            normals = info['cube'].NORMALS
            cube_verts = info['cube'].VERTICES
            verts = []
            for i in xrange(0, len(cube_verts), 3):
                verts.append(x + cube_verts[i] * size)
                verts.append(y + cube_verts[i + 1] * size)
                verts.append(z + cube_verts[i + 2] * size)

            indices = [i + info['index_offset'] for i in info['cube'].INDICES]
            return verts, normals, indices

        verts = []
        normals = []
        indices = []
        for child, child_info in self.iter_children_info(info):
            c_verts, c_normals, c_indices = child._generate_mesh(child_info)
            info['index_offset'] += len(c_verts) / 3
            verts.extend(c_verts)
            normals.extend(c_normals)
            indices.extend(c_indices)
        return verts, normals, indices

class _HeightMapLeaf(quadtree._QuadTreeLeaf):
    def generate_all_nodes(self, info, max_depth=None):
        return

    def get_points(self, info):
        return [Point(info['origin'].x, self._data, info['origin'].y)]

    def _generate_mesh(self, info):
        # generate mesh data for this point
        #
        x = info['origin'].x
        y = self._data
        z = info['origin'].y
        size = info['size']
        normals = info['cube'].NORMALS
        cube_verts = info['cube'].VERTICES
        verts = []
        for i in xrange(0, len(cube_verts), 3):
            verts.append(x + cube_verts[i] * size)
            verts.append(y + cube_verts[i + 1] * size)
            verts.append(z + cube_verts[i + 2] * size)

        indices = [i + info['index_offset'] for i in info['cube'].INDICES]
        return verts, normals, indices

class HeightMap(quadtree.QuadTree):
    INDENT = 0
    def __init__(self, size, max_height, max_depth, seed, base_height=0.0):
        self._seed = seed
        self._max_height = max_height
        self._base_height = base_height
        self._points = None
        super(HeightMap, self).__init__(size, max_depth)

    def generate_all_nodes(self, max_depth=None):
        self._root.generate_all_nodes(self._get_info(), max_depth=max_depth)

    def _create_root(self):
        root = self._BRANCH_CLS( self._base_height )
        root._children = [self._BRANCH_CLS( self._base_height ) for i in xrange(4)]
        return root

    def _get_info(self):
        info = super(HeightMap, self)._get_info()
        info['seed'] = self._seed
        return info

    def generate_mesh(self):
        from OpenGL import GL
        from ..data import cube
        from . import Mesh
        info = self._get_info()
        info['cube'] = cube
        info['index_offset'] = 0
        verts, normals, indices = self._root._generate_mesh(info)
        self.mesh = Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def render(self):
        from OpenGL import GL
        from ..game import GAME
        from . import Matrix
        with GAME.shaders['skin'] as shader:
            GL.glUniformMatrix4fv(
                shader.uniforms['modelToWorldMatrix'],
                1,
                GL.GL_FALSE,
                Matrix().tolist(),
            )
            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 1.0, 0.5, 1.0)
            self.mesh.render()

_HeightMapBranch._TREE_CLS = HeightMap
_HeightMapLeaf._TREE_CLS = HeightMap

HeightMap._BRANCH_CLS = _HeightMapBranch
HeightMap._LEAF_CLS = _HeightMapLeaf
