import random

import glfw

from . import quadtree
from . import Point

class _HeightMapNodeMixin(object):
    def _generate_debug_texture(self, info, textures):
        max_height = info['tree']._max_height
        # data range: -max_height to max_height
        color = (self._data + max_height) / (max_height*2.0)
        texture_index = 0
        row_size = 2**(info['level']-1)
        for depth, index in enumerate(info['parent_indices']+[info['index']]):
            size = row_size/(2**depth)
            if index & self._TREE_CLS._BITWISE_NUMS[0]:
                texture_index += size
            if index & self._TREE_CLS._BITWISE_NUMS[1]:
                texture_index += row_size * size

        texture_index *= 3
        textures[ info['level']-1 ][texture_index] = color
        textures[ info['level']-1 ][texture_index+1] = color
        textures[ info['level']-1 ][texture_index+2] = color

class _HeightMapBranch(quadtree._QuadTreeBranch, _HeightMapNodeMixin):
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
        corner_weights = [
            1.0,
            1.0,
            1.0,
            1.0,
        ]

        if child_info['index'] & self._TREE_CLS._BITWISE_NUMS[0]:
            """
            Child is in one of these spots:
                . x
                . x
            """
            corner_points[1].x += info['size']
            corner_points[3].x += info['size']

            corner_weights[1] += 1.0
            corner_weights[3] += 1.0
        else:
            """
            Child is in one of these spots:
                x .
                x .
            """
            corner_points[0].x -= info['size']
            corner_points[2].x -= info['size']

            corner_weights[0] += 1.0
            corner_weights[2] += 1.0

        if child_info['index'] & self._TREE_CLS._BITWISE_NUMS[1]:
            """
            Child is in one of these spots:
                x x
                . .
            """
            corner_points[2].y += info['size']
            corner_points[3].y += info['size']

            corner_weights[2] += 1.0
            corner_weights[3] += 1.0
        else:
            """
            Child is in one of these spots:
                . .
                x x
            """
            corner_points[0].y -= info['size']
            corner_points[1].y -= info['size']

            corner_weights[0] += 1.0
            corner_weights[1] += 1.0

        parent_height = 0.0
        for i, corner_point in enumerate(corner_points):
            if corner_point == info['origin']:
                corner_item = self
            else:
                corner_item = info['tree'].get_node(corner_point, max_depth=info['level'])[0]
                if corner_item is None:  # TODO: properly deal with edges
                    corner_item = info['tree']._root
            parent_height += corner_item._data * corner_weights[i]
        parent_height /= sum(corner_weights)

        rand = random.Random( info['seed'] )
        rand.jumpahead( (child_info['origin'].x, child_info['origin'].y) )  # jumpahead is expensive so only doing it once for both x and y

        # max_deviation = 1.0 / float(info['level']**2)
        # max_deviation = info['tree'].size() / 2**info['level']
        max_deviation = info['tree']._max_height / 2**(info['level']**0.92)
        deviation = rand.uniform(-max_deviation, max_deviation)
        return parent_height + deviation

    def generate_node(self, info, point, max_depth=None, child_info=None):
        if max_depth is not None and info['level'] >= max_depth:
            return self, info
        if info['origin'].x == point.x and info['origin'].y == point.y:
            return self, info

        if child_info is None:
            index = self.get_closest_child_index(info, point)
            child_info = self.get_child_info(info, index, copy=True)
        else:
            index = child_info['index']

        height = self._generate_node_height(info, point, child_info)
        if child_info['level'] >= info['tree'].max_depth():
            cls = self._TREE_CLS._LEAF_CLS
            self._children[index] = cls(height)
            return self._children[index], child_info
        else:
            cls = self._TREE_CLS._BRANCH_CLS
            self._children[index] = cls(height)
            return self._children[index].generate_node(child_info, point, max_depth)

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

    def generate(self, info, point):
        for child, child_info in self.iter_children_info(info):
            distance = point.distance( child_info['origin'] )
            max_distance = child_info['size'] * child_info['level']
            if distance <= max_distance:
                if child is None:
                    child, child_info = self.generate_node(info, child_info['origin'], max_depth=child_info['level'], child_info=child_info)
                child.generate(child_info, point)
            else:
                self._children[ child_info['index'] ] = None

    def _generate_debug_texture(self, info, textures):
        super(_HeightMapBranch, self)._generate_debug_texture(info, textures)
        for child, child_info in self.iter_children_info(info):
            try:
                child._generate_debug_texture(child_info, textures)
            except AttributeError:
                raise
                # TODO: implement for missing children
                # if child is not None:
                #     raise
                # super(_HeightMapBranch, self)._generate_debug_texture(child_info, textures)

class _HeightMapLeaf(quadtree._QuadTreeLeaf, _HeightMapNodeMixin):
    def _generate_all_nodes(self, info, max_depth=None):
        return

    def generate(self, info, point):
        return

    def get_points(self, info):
        return [Point(info['origin'].x, self._data, info['origin'].y)]

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
    INDENT = 0
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
        self._generate_debug_mesh()

    def _generate_all_nodes(self, max_depth=None):
        """Temporary debug function to generate all nodes to a certain depth
        """
        self._root._generate_all_nodes(self._get_info(), max_depth=max_depth)

    def _create_root(self):
        root = self._BRANCH_CLS( self._base_height )
        root._children = [self._BRANCH_CLS( self._base_height ) for i in xrange(4)]
        return root

    def _get_info(self):
        info = super(HeightMap, self)._get_info()
        info['seed'] = self._seed
        return info

    def _generate_debug_mesh(self):
        from OpenGL import GL
        from ..data import cube
        from . import Mesh
        info = self._get_info()
        info['cube'] = cube
        info['index_offset'] = 0
        verts, normals, indices = self._root._generate_debug_mesh(info)
        self.mesh = Mesh(verts, normals, indices, GL.GL_TRIANGLES)

    def _generate_debug_texture(self):
        from OpenGL import GL
        from . import FLOAT_SIZE
        info = self._get_info()
        self._render_depth = 0
        self._texture_data = [[0.0 for j in xrange(((2**i)**2)*3)] for i in xrange(self._max_depth)]
        self._root._generate_debug_texture(info, self._texture_data)
        verts = [
            -1.0,  1.0, 0.0,
             1.0,  1.0, 0.0,
             1.0, -1.0, 0.0,
            -1.0, -1.0, 0.0,
        ]
        uvs = [
            0.0, 1.0,
            1.0, 1.0,
            1.0, 0.0,
            0.0, 0.0,
        ]

        self._vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self._vao)

        # generate vertex position buffer
        #
        vertexBufferObject = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertexBufferObject)

        array_type = (GL.GLfloat*len(verts))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(verts)*FLOAT_SIZE,
            array_type(*verts),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(
            0,              # attribute 0. No particular reason for 0, but must match the layout in the shader.
            3,              # size
            GL.GL_FLOAT,    # type
            GL.GL_FALSE,    # normalized?
            0,              # stride (offset from start of data)
            None            # array buffer offset
        )

        # generate vertex uv buffer
        #
        uvBufferObject = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, uvBufferObject)

        array_type = (GL.GLfloat*len(uvs))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(uvs)*FLOAT_SIZE,
            array_type(*uvs),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(
            1,              # attribute 1. No particular reason for 1, but must match the layout in the shader.
            2,              # size
            GL.GL_FLOAT,    # type
            GL.GL_FALSE,    # normalized?
            0,              # stride (offset from start of data)
            None            # array buffer offset
        )

        GL.glBindVertexArray(0)

        # Create one OpenGL textures
        self._textures = []
        for i in xrange(self.max_depth()):
            self._textures.append( GL.glGenTextures(1) )

            # "Bind" the newly created texture : all future texture functions will modify this texture
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._textures[i])

            # Give the image to OpenGL
            array_type = (GL.GLfloat*len(self._texture_data[i]))
            GL.glTexImage2D(
                GL.GL_TEXTURE_2D,
                0,
                GL.GL_RGB,
                2**i,
                2**i,
                0,
                GL.GL_RGB,
                GL.GL_FLOAT,
                array_type(*self._texture_data[i])
            )

            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
            GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)

    def handle_input(self):
        from ..game import GAME
        if not hasattr(self, '_handled_keys'):
            self._handled_keys = set()
        if glfw.KEY_DOWN in GAME.pressed_keys:
            if glfw.KEY_DOWN not in self._handled_keys:
                self._render_depth -= 1
                if self._render_depth < 0:
                    self._render_depth = 0
                self._handled_keys.add(glfw.KEY_DOWN)
        elif glfw.KEY_DOWN in self._handled_keys:
            self._handled_keys.remove(glfw.KEY_DOWN)

        if glfw.KEY_UP in GAME.pressed_keys:
            if glfw.KEY_UP not in self._handled_keys:
                self._render_depth += 1
                if self._render_depth >= len(self._textures):
                    self._render_depth = len(self._textures)-1
                self._handled_keys.add(glfw.KEY_UP)
        elif glfw.KEY_UP in self._handled_keys:
            self._handled_keys.remove(glfw.KEY_UP)

    def render(self):
        from OpenGL import GL
        from ..game import GAME
        with GAME.shaders['heightmap'] as shader:
            # Bind our texture in Texture Unit 0
            GL.glActiveTexture(GL.GL_TEXTURE0)
            GL.glBindTexture(GL.GL_TEXTURE_2D, self._textures[self._render_depth])
            # Set our "myTextureSampler" sampler to user Texture Unit 0
            GL.glUniform1i(shader.uniforms['textureSampler'], 0)

            GL.glBindVertexArray(self._vao)
            GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 4)  # Starting from vertex 0; 4 vertices total -> 2 triangles
            GL.glBindVertexArray(0)

        # from OpenGL import GL
        # from ..game import GAME
        # from . import Matrix
        # with GAME.shaders['skin'] as shader:
        #     GL.glUniformMatrix4fv(
        #         shader.uniforms['modelToWorldMatrix'],
        #         1,
        #         GL.GL_FALSE,
        #         Matrix().tolist(),
        #     )
        #     GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 1.0, 0.5, 1.0)
        #     self.mesh.render()

_HeightMapBranch._TREE_CLS = HeightMap
_HeightMapLeaf._TREE_CLS = HeightMap

HeightMap._BRANCH_CLS = _HeightMapBranch
HeightMap._LEAF_CLS = _HeightMapLeaf
