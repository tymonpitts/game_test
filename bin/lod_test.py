#! /usr/bin/python
from __future__ import print_function

import os

import glfw
import numpy
from OpenGL import GL
import OpenImageIO
from typing import Dict, List, Tuple

import game_core
from game_core import FLOAT_SIZE
from game_core import decorators
from tempest.data.lod_transition_proof_of_concept import smooth_cube
from tempest import shaders


class Camera(game_core.AbstractCamera):
    def __init__(self, position=None):
        super(Camera, self).__init__(position)
        self.acceleration_rate = 10.0
        self.max_speed = 10.0

        # store the last position of the cursor so we can compute how far
        # the cursor moved since the last time we integrated. This will
        # allow us to determine how much to rotate the camera.
        self._last_cursor_position = None  # type: Tuple[float, float]

    def integrate(self, time, delta_time, window):
        # type: (float, float, Window) -> None

        # determine how far the cursor has moved since the last time
        # we integrated. Store the new cursor position so we can do this
        # again next time we integrate.
        cursor_position = glfw.get_cursor_pos(window.window)
        if self._last_cursor_position is None:
            cursor_movement = (0.0, 0.0)
            self._last_cursor_position = cursor_position
        else:
            cursor_movement = (
                cursor_position[0] - self._last_cursor_position[0],
                cursor_position[1] - self._last_cursor_position[1],
            )
            self._last_cursor_position = cursor_position

        # turn the cursor movement into rotational values
        self._rotx -= cursor_movement[1] * 0.01
        self._rotx = self.clamp_angle(self._rotx)
        self._roty -= cursor_movement[0] * 0.01
        ry = self._get_roty_matrix()
        rx = self._get_rotx_matrix()

        # turn key presses into translation values and add that translation
        # to this camera's world position
        translate = game_core.Vector()
        if glfw.KEY_W in window.pressed_keys:
            translate.z -= self.acceleration_rate
        if glfw.KEY_S in window.pressed_keys:
            translate.z += self.acceleration_rate
        if glfw.KEY_A in window.pressed_keys:
            translate.x -= self.acceleration_rate
        if glfw.KEY_D in window.pressed_keys:
            translate.x += self.acceleration_rate
        if glfw.KEY_SPACE in window.pressed_keys:
            translate.y += self.acceleration_rate
        if glfw.KEY_LEFT_SHIFT in window.pressed_keys:
            translate.y -= self.acceleration_rate
        translate *= delta_time
        translate *= ry
        self._pos += translate

        # resolve orientation and position components to a full matrix
        self.matrix = rx * ry
        for i in xrange(3):
            self.matrix[3, i] = self._pos[i]


class Window(game_core.AbstractWindow):
    def __init__(self):
        super(Window, self).__init__()
        self.title = 'LOD Test'
        self.cube = None  # type: game_core.Mesh
        self.shaders = None  # type: Dict[str, game_core.ShaderProgram]
        self.camera = None  # type: Camera
        self.lod_tree = None  # type: LodTestTree
        self.light_direction = None  # type: game_core.Vector
        self.lod_distances = [
            256.0,
            90.0,
            64.0,
            45.0,
            32.0,
            22.0,
            16.0,
        ]  # distances at which each LOD level is at its finest

    def init(self):
        super(Window, self).init()

        # hide the cursor and lock it to this window. GLFW will then take care
        # of all the details of cursor re-centering and offset calculation and
        # providing the application with a virtual cursor position
        glfw.set_input_mode(self.window, glfw.CURSOR, glfw.CURSOR_DISABLED)

        self.cube = game_core.Mesh(smooth_cube.VERTICES, smooth_cube.NORMALS, smooth_cube.INDICES, smooth_cube.DRAW_METHOD)

        self.shaders = shaders.init()

        # set a default matrix for models, otherwise its nothing apparently
        self.light_direction = game_core.Vector(0.1, 1.0, 0.5)
        self.light_direction.normalize()
        model_mat = game_core.Matrix()
        for name, shader in self.shaders.iteritems():
            if 'modelToWorldMatrix' in shader.uniforms:
                with shader:
                    GL.glUniformMatrix4fv(
                        shader.uniforms['modelToWorldMatrix'],
                        1,
                        GL.GL_FALSE,
                        model_mat.tolist()
                    )
            if 'dirToLight' in shader.uniforms:
                with shader:
                    GL.glUniform4fv(shader.uniforms['dirToLight'], 1, list(self.light_direction))
            # if 'diffuseColor' in shader.uniforms:
            #     with shader:
            #         GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)

        self.camera = Camera(position=[0.0, 32.0, 128.0])
        self.camera.init(*glfw.get_framebuffer_size(self.window))
        self._set_perspective_matrix()

        self.lod_tree = LodTestTree(size=64.0, max_depth=6)
        self.lod_tree.init()

        for depth in range(self.lod_tree.max_depth):
            fine_distance = self.lod_distances[depth]
            if depth == 0:
                coarse_distance = fine_distance * 2.0
            else:
                coarse_distance = self.lod_distances[depth - 1]
            with self.shaders['lod_test_{}'.format(depth)] as shader:
                GL.glUniform1f(shader.uniforms['fineDistance'], fine_distance)
                GL.glUniform1f(shader.uniforms['coarseDistance'], coarse_distance)

    def _set_perspective_matrix(self):
        # TODO: move this to camera's reshape
        projection_matrix = self.camera.projection_matrix.tolist()
        for name, shader in self.shaders.iteritems():
            if 'cameraToClipMatrix' in shader.uniforms:
                with shader:
                    GL.glUniformMatrix4fv(
                        shader.uniforms['cameraToClipMatrix'],
                        1,
                        GL.GL_FALSE,
                        projection_matrix,
                    )

    def reshape(self, w, h):
        super(Window, self).reshape(w, h)
        self.camera.reshape(w, h)
        self._set_perspective_matrix()

    def integrate(self, t, delta_time):
        # # FOR DEBUGGING
        # if not hasattr(self, 'display_depth'):
        #     self.display_depth = 0.0
        #     self.transition_rate = 0.25
        #     self.base_visible = True
        # if glfw.KEY_UP in self.pressed_keys:
        #     self.display_depth -= 1.0 * self.transition_rate
        #     self.display_depth = max(self.display_depth, 0)
        # if glfw.KEY_DOWN in self.pressed_keys:
        #     self.display_depth += 1.0 * self.transition_rate
        #     self.display_depth = min(self.display_depth, self.lod_tree.max_depth)
        # if glfw.KEY_V in self.pressed_keys:
        #     print('toggling base visible')
        #     self.base_visible = not self.base_visible
        #     print('  {}'.format(self.base_visible))

        # # FOR DEBUGGING
        # if not hasattr(self, 'display_depth'):
        #     self.display_depth = 0
        #     self.coarsness = 1.0
        #     self.transition_rate = 1.0
        # if glfw.KEY_LEFT in self.pressed_keys:
        #     self.coarsness -= delta_time * self.transition_rate
        #     if self.coarsness < 0.0:
        #         self.display_depth += 1
        #         self.coarsness = 1.0 + self.coarsness
        #         if self.display_depth > self.lod_tree.max_depth:
        #             self.display_depth = self.lod_tree.max_depth
        #             self.coarsness = 0.0
        #     print('integrate:')
        #     print('  display_depth: {}'.format(self.display_depth))
        #     print('  coarsness: {}'.format(self.coarsness))
        # elif glfw.KEY_RIGHT in self.pressed_keys:
        #     self.coarsness += delta_time * self.transition_rate
        #     if self.coarsness > 1.0:
        #         self.display_depth -= 1
        #         self.coarsness = 0.0 + (1.0 - self.coarsness)
        #         if self.display_depth < 0:
        #             self.display_depth = 0
        #             self.coarsness = 1.0
        #     print('integrate:')
        #     print('  display_depth: {}'.format(self.display_depth))
        #     print('  coarsness: {}'.format(self.coarsness))
        # for shader in self.shaders.itervalues():
        #     if 'coarsness' in shader.uniforms:
        #         with shader:
        #             GL.glUniform1f(shader.uniforms['coarsness'], self.coarsness)

        self.camera.integrate(t, delta_time, self)

        # TODO: move this to camera's integrate
        i_cam_mat = self.camera.matrix.inverse().tolist()
        camera_world_position = list(self.camera._pos)
        for shader in self.shaders.itervalues():
            if 'worldToCameraMatrix' in shader.uniforms:
                with shader:
                    GL.glUniformMatrix4fv(
                        shader.uniforms['worldToCameraMatrix'],
                        1,
                        GL.GL_FALSE,
                        i_cam_mat
                    )
            if 'cameraWorldPosition' in shader.uniforms:
                with shader:
                    GL.glUniform4fv(
                        shader.uniforms['cameraWorldPosition'],
                        1,
                        camera_world_position
                    )

    def draw(self):
        # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        self.lod_tree.draw(self)

        # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        # with self.shaders['simple']:
        #     self.cube.render()
        # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)


class LodTestItem(game_core.TreeNode):
    def get_item_value(self):
        return self.get_value()[0]

    def get_position(self):
        return self.get_value()[1]

    def set_item_value(self, value):
        self.get_value()[0] = value

    def set_position(self, vertexes):
        self.get_value()[1] = vertexes

    def init_position(self):
        if self.is_leaf():
            # position was already initialized during item creation from heightmap
            # if self.get_item_value() is not None:
            #     self.set_position(self.get_origin())
            return

        # initialize position based on an average of child positions
        child_x_positions = []  # type: List[float]
        child_y_positions = []  # type: List[float]
        child_z_positions = []  # type: List[float]
        children = self.get_children()
        for i, child in enumerate(children):
            child_position = child.get_position()
            if child_position:
                child_x_positions.append(child_position.x)
                child_y_positions.append(child_position.y)
                child_z_positions.append(child_position.z)

        x = sum(child_x_positions) / len(child_x_positions)
        y = sum(child_x_positions) / len(child_y_positions)
        z = sum(child_x_positions) / len(child_z_positions)
        self.set_position(game_core.Point(x, y, z))

    @decorators.cached_method
    def is_vertex_item(self):
        if not self.get_item_value():
            return False

        # TODO: this doesn't handle branches
        for neighbor in self.get_neighbors():
            # only create vertexes for items that neighbor an empty
            # space. There is no need to create vertexes for items that
            # are surrounded by other items with data
            if neighbor is None or neighbor.get_item_value() is None:
                return True
        return False


class LodTestTree(game_core.Octree):
    def __init__(self, size, max_depth):
        super(LodTestTree, self).__init__(size, max_depth)
        self.gl_vertex_array = None  # type: int
        self.gl_vertex_array_num_indexes = None  # type: int
        self.gl_point_vertex_array = None  # type: int
        self.gl_point_vertex_array_num_vertexes = None  # type: int

    def _get_default_node_data(self):
        return [None, None]

    def _create_node_proxy(self, data, parent=None, index=0):
        """
        Returns:
            TreeNode
        """
        return LodTestItem(data, tree=self, parent=parent, index=index)

    def create_texture_vao(self):
        # type: () -> int
        """ If we want to draw the heightmap texture then use this function
        to generate a vertex array object to store a quad to draw the texture on
        """
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

        texture_quad_vao = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(texture_quad_vao)

        # generate vertex position buffer
        #
        vertexBufferObject = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertexBufferObject)

        array_type = (GL.GLfloat*len(verts))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(verts) * game_core.FLOAT_SIZE,
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
            len(uvs) * game_core.FLOAT_SIZE,
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
        return texture_quad_vao

    def init(self):
        height_map_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'BritanniaHeightMap2.exr'))
        image_buf = OpenImageIO.ImageBuf(height_map_path, 0, 7)  # 8k image so miplevel 7 should be 64
        assert 2 ** self.max_depth == image_buf.spec().width

        # # initialize the heightmap GL texture
        # self.texture_quad_vao = self.create_texture_vao()
        # self.texture = GL.glGenTextures(1)  # type: int
        # GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        #
        # # Give the image to OpenGL
        # data = image_buf.get_pixels(OpenImageIO.FLOAT).flatten()
        # array_type = (GL.GLfloat * len(data))
        # GL.glTexImage2D(
        #     GL.GL_TEXTURE_2D,  # target
        #     0,  # mipmap level
        #     GL.GL_RGB,  # internalformat: number of color components in the texture
        #     image_buf.spec().width,  # width
        #     image_buf.spec().height,  # height
        #     0,  # border (must be 0 according to OpenGL docs)
        #     GL.GL_RGB,  # format of the pixel data
        #     GL.GL_FLOAT,  # data type of the pixel data
        #     array_type(*data)
        # )
        #
        # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MAG_FILTER, GL.GL_NEAREST)
        # GL.glTexParameteri(GL.GL_TEXTURE_2D, GL.GL_TEXTURE_MIN_FILTER, GL.GL_NEAREST)
        # return

        root = self.get_root()  # type: LodTestItem

        print('generating items...')
        items = [root]  # type: List[LodTestItem]
        items_by_depth = [list() for i in range(self.max_depth + 1)]  # type: List[List[LodTestItem]]
        items_by_depth[0].append(root)
        printed_depth = -1
        while items:
            item = items.pop(0)
            if printed_depth != item.get_depth():
                printed_depth = item.get_depth()
                print('  working on level {} items: {}'.format(printed_depth, item.index_hierarchy()))

            # determine this item's bounds in the image's space. The image
            # should have the same dimensions as the tree but the tree's
            # origin is in the center whereas the image's is in the bottom
            # left corner (possibly top left?) so the item's center needs to
            # be translated.
            half_size = self.size / 2.0
            tree_to_image_translation = game_core.Point(half_size, 0.0, half_size)
            item_bounds = item.get_bounds()
            bounds_in_image_min = (item_bounds.min() + tree_to_image_translation)
            bounds_in_image_max = (item_bounds.max() + tree_to_image_translation)

            # using the item's bounds in image space computed above, compute
            # stats about the image's pixels within this space
            region_of_interest = OpenImageIO.ROI(
                int(bounds_in_image_min.x), int(bounds_in_image_max.x) + 1,  # x min/max
                int(bounds_in_image_min.z), int(bounds_in_image_max.z) + 1,  # y min/max
                0, 1,  # z min/max
                0, 1,  # channel begin/end (exclusive)
            )
            stats = OpenImageIO.ImageBufAlgo.computePixelStats(
                image_buf,
                region_of_interest,
                2,  # nthreads
            )

            # the stats computed above contain min/max pixel values which
            # correspond to min/max height for the tree. However, we don't
            # want the heightmap to go all the way to the top of the tree
            # since that will make it look very tall so we'll scale the
            # min/max height to only be 1/8 the size of the tree. We also want
            # the heightmap to be centered around the tree's origin so
            # heightmap=0 should be below the tree's origin
            # NOTE: to avoid precision issues we round the computed values to
            #       2 decimal places
            max_height = self.size / 8.0
            half_max_height = max_height / 2.0
            image_min_height = round((stats.min[0] * max_height) - half_max_height, 2)
            image_max_height = round((stats.max[0] * max_height) - half_max_height, 2)

            # if the item is not within the min/max height range computed
            # from the heightmap image then this is an empty item so move on
            # NOTE: if an item's min bounds equals the max height then we
            #       consider the item but if the item's max bounds equals the
            #       min height then the item is empty so 2 items don't double up
            #       on the boundaries
            if image_max_height < bounds_in_image_min.y:
                continue
            elif image_min_height >= bounds_in_image_max.y:
                # TODO: add items underneath height map too but not super fine detail items
                continue

            # if we aren't at the tree's max depth then split the item and
            # add the children to the list of items to process. Otherwise
            # this is a leaf level item so give it a value and add it to the
            # list of items to contribute to the mesh
            items_by_depth[item.get_depth()].append(item)
            if item.get_depth() < self.max_depth:
                item.split()
                items.extend(item.get_children())
            else:
                item.set_item_value('foo')
                position = item.get_origin()
                position.y = image_max_height
                item.set_position(position)

        # # FOR DEBUGGING
        # # create a single mesh for all items
        # print('initialziing cage meshes...')
        # self.cage_mesh_gl_vertex_arrays = []
        # self.cage_mesh_num_indexes = []
        # for depth in range(self.max_depth + 1):
        #     print('  working on level {} mesh:'.format(depth))
        #     verts = []  # List[float]
        #     normals = []  # List[float]
        #     indexes = []  # List[int]
        #     vert_count = 0
        #     for item in items_by_depth[depth]:
        #         if not item.get_item_value() and not item.get_children():
        #             continue
        #         for i in range(8):
        #             cube_vert = game_core.Vector(
        #                 smooth_cube.VERTICES[i * 3],
        #                 smooth_cube.VERTICES[i * 3 + 1],
        #                 smooth_cube.VERTICES[i * 3 + 2],
        #             )
        #             vert = item.get_origin() + cube_vert * item.get_size()
        #             verts.append(vert.x)
        #             verts.append(vert.y)
        #             verts.append(vert.z)
        #
        #             cube_normal = game_core.Vector(
        #                 smooth_cube.NORMALS[i * 3],
        #                 smooth_cube.NORMALS[i * 3 + 1],
        #                 smooth_cube.NORMALS[i * 3 + 2],
        #             )
        #             normals.append(cube_normal.x)
        #             normals.append(cube_normal.y)
        #             normals.append(cube_normal.z)
        #
        #         indexes.extend([i + vert_count for i in smooth_cube.INDICES])
        #         vert_count += 8
        #
        #     vertex_array = GL.glGenVertexArrays(1)
        #     self.cage_mesh_gl_vertex_arrays.append(vertex_array)
        #     GL.glBindVertexArray(vertex_array)
        #     root.set_gl_vertex_array(vertex_array)
        #     vertex_buffer = GL.glGenBuffers(1)
        #     GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        #     data = verts + normals + [0.0 for v in verts] + [0.0 for n in normals]
        #     array_type = (GL.GLfloat*len(data))
        #     GL.glBufferData(
        #             GL.GL_ARRAY_BUFFER,
        #             len(data)*FLOAT_SIZE,
        #             array_type(*data),
        #             GL.GL_STATIC_DRAW
        #     )
        #     GL.glEnableVertexAttribArray(0)
        #     GL.glEnableVertexAttribArray(1)
        #     GL.glEnableVertexAttribArray(2)
        #     GL.glEnableVertexAttribArray(3)
        #     GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        #     GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(verts)*FLOAT_SIZE))
        #     GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(verts)*2*FLOAT_SIZE))
        #     GL.glVertexAttribPointer(3, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(verts)*3*FLOAT_SIZE))
        #
        #     index_buffer = GL.glGenBuffers(1)
        #     GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, index_buffer)
        #     self.cage_mesh_num_indexes.append(len(indexes))
        #     array_type = (GL.GLuint*len(indexes))
        #     GL.glBufferData(
        #             GL.GL_ELEMENT_ARRAY_BUFFER,
        #             len(indexes)*FLOAT_SIZE,
        #             array_type(*indexes),
        #             GL.GL_STATIC_DRAW
        #     )
        #
        #     GL.glBindVertexArray(0)
        # return

        print('initializing item positions...')
        # NOTE: we do this in reverse depth order since parents derive
        #       their positions from children
        for depth_items in reversed(items_by_depth):
            print('  working on level {} items'.format(depth_items[0].get_depth()))
            for item in depth_items:
                item.init_position()

        # # FOR DEBUGGING
        # # create a single mesh for all items
        # print('initialziing meshes...')
        # self.mesh_gl_vertex_arrays = []
        # self.mesh_num_indexes = []
        # for depth in range(self.max_depth + 1):
        #     print('  working on level {} mesh:'.format(depth))
        #     verts = []  # List[float]
        #     normals = []  # List[float]
        #     indexes = []  # List[int]
        #     vert_count = 0
        #     for item in items_by_depth[depth]:
        #         if not item.get_item_value() and not item.get_children():
        #             continue
        #         vertexes = item.get_position()
        #         verts.extend([v.pos[i] for v in vertexes for i in range(3)])
        #         normals.extend([v.normal[i] for v in vertexes for i in range(3)])
        #         indexes.extend([i + vert_count for i in smooth_cube.INDICES])
        #         vert_count += 8
        #
        #     vertex_array = GL.glGenVertexArrays(1)
        #     self.mesh_gl_vertex_arrays.append(vertex_array)
        #     GL.glBindVertexArray(vertex_array)
        #     root.set_gl_vertex_array(vertex_array)
        #     vertex_buffer = GL.glGenBuffers(1)
        #     GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        #     data = verts + normals + [0.0 for v in verts] + [0.0 for n in normals]
        #     array_type = (GL.GLfloat*len(data))
        #     GL.glBufferData(
        #             GL.GL_ARRAY_BUFFER,
        #             len(data)*FLOAT_SIZE,
        #             array_type(*data),
        #             GL.GL_STATIC_DRAW
        #     )
        #     GL.glEnableVertexAttribArray(0)
        #     GL.glEnableVertexAttribArray(1)
        #     GL.glEnableVertexAttribArray(2)
        #     GL.glEnableVertexAttribArray(3)
        #     GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        #     GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(verts)*FLOAT_SIZE))
        #     GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(verts)*2*FLOAT_SIZE))
        #     GL.glVertexAttribPointer(3, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(verts)*3*FLOAT_SIZE))
        #
        #     index_buffer = GL.glGenBuffers(1)
        #     GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, index_buffer)
        #     self.mesh_num_indexes.append(len(indexes))
        #     array_type = (GL.GLuint*len(indexes))
        #     GL.glBufferData(
        #             GL.GL_ELEMENT_ARRAY_BUFFER,
        #             len(indexes)*FLOAT_SIZE,
        #             array_type(*indexes),
        #             GL.GL_STATIC_DRAW
        #     )
        #
        #     GL.glBindVertexArray(0)
        # return

        self.generate_mesh(game_core.Point())  # TODO: generate with proper camera position
        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)

    def generate_mesh(self, camera_position):
        print('generating mesh...')
        vertex_items = []  # type: List[LodTestItem]
        loop_items = [self.get_root()]  # type: List[LodTestItem]
        while loop_items:
            item = loop_items.pop(0)
            if item.is_branch():
                loop_items.extend(item.get_children())
                continue

            if not item.is_vertex_item():
                continue

            normal = game_core.Vector()
            normal_offset = -1.0
            for i, neighbor in enumerate(item.get_neighbors()):
                if neighbor is None or not neighbor.is_vertex_item():
                    neighbor_dimension = int(i / 2)
                    # TODO: this doesn't work for single item thick walls/floors. Need double sided faces or something
                    if normal[neighbor_dimension]:
                        normal[neighbor_dimension] += normal_offset
                    else:
                        normal[neighbor_dimension] = 1.0
                normal_offset *= -1.0

            if normal:
                item.normal = normal.normal()  # TODO: store this somewhere better?
                item.vertex_index = len(vertex_items)
                vertex_items.append(item)

        positions_data = []  # type: List[float]
        normals_data = []  # type: List[float]
        coarse_position_vectors_data = []  # type: List[float]
        coarse_normal_vectors_data = []  # type: List[float]
        indexes_data = []  # type: List[int]
        for item in vertex_items:
            # add a vertex position to the array
            position = item.get_position()
            positions_data.append(position.x)
            positions_data.append(position.y)
            positions_data.append(position.z)

            normals_data.append(item.normal.x)
            normals_data.append(item.normal.y)
            normals_data.append(item.normal.z)

            coarse_position_vector = position - item.parent.get_position()
            coarse_position_vectors_data.append(coarse_position_vector.x)
            coarse_position_vectors_data.append(coarse_position_vector.y)
            coarse_position_vectors_data.append(coarse_position_vector.z)

            # TODO: figure out parent normals properly
            # coarse_normal_vector = item.normal - item.parent.normal
            coarse_normal_vector = item.normal
            coarse_normal_vectors_data.append(coarse_normal_vector.x)
            coarse_normal_vectors_data.append(coarse_normal_vector.y)
            coarse_normal_vectors_data.append(coarse_normal_vector.z)

            # connect to neighbors in the positive direction.
            # neighbors in the negative direction will be connected
            # when that neighbor connects to its neighbors in the
            # positive direction
            positive_neighbors = item.get_neighbors()[1::2]  # type: List[LodTestItem]
            for neighbor_dimension, neighbor in enumerate(positive_neighbors):
                if not hasattr(neighbor, 'vertex_index'):
                    continue
                for dimension_offset in (1, 2):
                    normal_dimension = neighbor_dimension + dimension_offset
                    if normal_dimension >= self.DIMENSIONS:
                        normal_dimension -= self.DIMENSIONS

                    if not item.normal[normal_dimension] or not neighbor.normal[normal_dimension]:
                        continue
                    if numpy.sign(item.normal[normal_dimension]) != numpy.sign(neighbor.normal[normal_dimension]):
                        continue

                    other_neighbor_dimension = neighbor_dimension - dimension_offset
                    if other_neighbor_dimension < 0:
                        other_neighbor_dimension = self.DIMENSIONS - 1
                    other_neighbor = neighbor.get_neighbors()[(other_neighbor_dimension * 2) + 1]
                    if not hasattr(other_neighbor, 'vertex_index'):
                        continue

                    indexes_data.append(item.vertex_index)
                    if dimension_offset == 1:
                        indexes_data.append(neighbor.vertex_index)
                        indexes_data.append(other_neighbor.vertex_index)
                    else:
                        indexes_data.append(other_neighbor.vertex_index)
                        indexes_data.append(neighbor.vertex_index)

            # TODO: add faces for diagonal neighbor to corner neighbor

        # vertex_neighbor_lists = []
        # for vertex_index, item in enumerate(list(vertex_items)):
        #     vertex_neighbors = []
        #     for neighbor in item.get_diagonal_neighbors():
        #         try:
        #             neighbor_vertex_index = vertex_items.index(neighbor)
        #         except IndexError:
        #             continue
        #         if neighbor in item.get_neighbors():
        #             vertex_neighbors.append(neighbor)
        #         else:
        #
        #         vertex_neighbors.append(neighbor_index)
        #
        #     if len(vertex_neighbors) <= 1:
        #         vertex_items.remove(item)
        #
        # positions_data = []  # type: List[float]
        # normals_data = []  # type: List[float]
        # coarse_position_vectors_data = []  # type: List[float]
        # coarse_normal_vectors_data = []  # type: List[float]
        # indexes_data = []  # type: List[int]
        # for vertex_index, item in enumerate(vertex_items):
        #     # add a vertex position to the array
        #     position = item.get_position()
        #     positions_data.append(position.x)
        #     positions_data.append(position.y)
        #     positions_data.append(position.z)
        #
        #     # find all vertexes we should be connecting to by looking at
        #     # adjacent (both directly and diagonally) items that are also
        #     # contributing vertexes
        #     vertex_neighbors = []
        #     for neighbor in item.get_diagonal_neighbors():
        #         try:
        #             neighbor_index = vertex_items.index(neighbor)
        #         except IndexError:
        #             continue
        #         vertex_neighbors.append(neighbor_index)
        #
        #     if len(vertex_neighbors)

        self.gl_vertex_array_num_indexes = len(indexes_data)
        if self.gl_vertex_array is None:
            self.gl_vertex_array = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.gl_vertex_array)
        vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        data = positions_data + normals_data + coarse_position_vectors_data + coarse_normal_vectors_data
        array_type = (GL.GLfloat*len(data))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(data)*FLOAT_SIZE,
            array_type(*data),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glEnableVertexAttribArray(2)
        GL.glEnableVertexAttribArray(3)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(positions_data)*FLOAT_SIZE))
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(positions_data)*2*FLOAT_SIZE))
        GL.glVertexAttribPointer(3, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(positions_data)*3*FLOAT_SIZE))

        index_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, index_buffer)
        array_type = (GL.GLuint*len(indexes_data))
        GL.glBufferData(
            GL.GL_ELEMENT_ARRAY_BUFFER,
            len(indexes_data)*FLOAT_SIZE,
            array_type(*indexes_data),
            GL.GL_STATIC_DRAW
        )

        self.gl_point_vertex_array_num_vertexes = len(vertex_items)
        if self.gl_point_vertex_array is None:
            self.gl_point_vertex_array = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.gl_point_vertex_array)
        vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        data = positions_data
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

    def draw(self, window):
        # type: (Window) -> None
        # # FOR DEBUGGING
        # # draw single mesh
        # depth = int(math.floor(getattr(window, 'display_depth', 0.0)))
        # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        # with window.shaders['lod_test_{}'.format(depth)]:
        #     GL.glBindVertexArray(self.mesh_gl_vertex_arrays[depth])
        #     GL.glDrawElements(smooth_cube.DRAW_METHOD, self.mesh_num_indexes[depth], GL.GL_UNSIGNED_INT, None)
        #     GL.glBindVertexArray(0)
        # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)
        # if getattr(window, 'base_visible', True):
        #     with window.shaders['lod_test_{}'.format(self.max_depth)]:
        #         GL.glBindVertexArray(self.mesh_gl_vertex_arrays[self.max_depth])
        #         GL.glDrawElements(smooth_cube.DRAW_METHOD, self.mesh_num_indexes[self.max_depth], GL.GL_UNSIGNED_INT, None)
        #         GL.glBindVertexArray(0)
        # return

        # # draw the heightmap
        # with window.shaders['heightmap'] as shader:
        #     # Bind our texture in Texture Unit 0
        #     GL.glActiveTexture(GL.GL_TEXTURE0)
        #     GL.glBindTexture(GL.GL_TEXTURE_2D, self.texture)
        #     # Set our "myTextureSampler" sampler to user Texture Unit 0
        #     GL.glUniform1i(shader.uniforms['textureSampler'], 0)
        #
        #     GL.glBindVertexArray(self.texture_quad_vao)
        #     GL.glDrawArrays(GL.GL_TRIANGLE_FAN, 0, 4)  # Starting from vertex 0; 4 vertices total -> 2 triangles
        #     GL.glBindVertexArray(0)
        # return

        with window.shaders['lod_test_0']:
            GL.glBindVertexArray(self.gl_vertex_array)
            GL.glDrawElements(GL.GL_TRIANGLES, self.gl_vertex_array_num_indexes, GL.GL_UNSIGNED_INT, None)
            GL.glBindVertexArray(0)

        # with window.shaders['point']:
        #     GL.glBindVertexArray(self.gl_point_vertex_array)
        #     GL.glDrawArrays(GL.GL_POINTS, 0, self.gl_point_vertex_array_num_vertexes)
        #     GL.glBindVertexArray(0)

        # # FOR DEBUGGING
        # items = [self.get_root()]  # type: List[LodTestItem]
        # while items:
        #     item = items.pop(0)
        #     if item.get_depth() < window.display_depth:
        #         items.extend(item.get_children())
        #     else:
        #         item.draw(window)


if __name__ == '__main__':
    Window().run()
