#! /usr/bin/python
from __future__ import print_function

import os

import glfw
from OpenGL import GL
import OpenImageIO

from typing import Dict, List, Tuple

import game_core
from game_core import FLOAT_SIZE
from tempest.data.lod_transition_proof_of_concept import smooth_cube
from tempest import shaders


class Camera(game_core.AbstractCamera):
    def __init__(self, position=None):
        super(Camera, self).__init__(position)
        self.acceleration_rate = 1.0

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
        self.distance_to_camera = None  # type: float
        self.transition_end_distance = 2.0
        self.transition_range = 3.0
        self.level = 0
        self.transition_progress = 0.0  # type: float

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
            if 'diffuseColor' in shader.uniforms:
                with shader:
                    GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)

        self.camera = Camera(position=[0.0, 0.0, 1.5])
        self.camera.init(*glfw.get_framebuffer_size(self.window))
        self._set_perspective_matrix()

        self.lod_tree = LodTestTree(size=64.0, max_depth=6)
        self.lod_tree.init()
        for depth in range(self.lod_tree.max_depth):
            depth_size = math.pow(self.lod_tree.size, 1.0 / (depth + 1.0))
            transition_end_distance = depth_size
            transition_range = depth_size
            with self.shaders['lod_test_{}'.format(depth)] as shader:
                GL.glUniform1f(shader.uniforms['transitionEndDistance'], transition_end_distance)
                GL.glUniform1f(shader.uniforms['transitionRange'], transition_range)

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
        if glfw.KEY_UP in self.pressed_keys:
            self.level = min(self.level + 1, 1)
        elif glfw.KEY_DOWN in self.pressed_keys:
            self.level = max(self.level - 1, 0)
        if glfw.KEY_LEFT in self.pressed_keys:
            self.transition_progress = max(self.transition_progress - delta_time, 0.0)
        elif glfw.KEY_RIGHT in self.pressed_keys:
            self.transition_progress = min(self.transition_progress + delta_time, 1.0)

        self.camera.integrate(t, delta_time, self)
        self.distance_to_camera = (game_core.Point() * self.camera.matrix).distance(self.lod_tree.get_root().get_origin())

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
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        self.lod_tree.draw(self)

        # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        # with self.shaders['simple']:
        #     self.cube.render()
        # GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)


class TransitionVertex(object):
    def __init__(self, pos, normal, pos_vector=None, normal_vector=None):
        # type: (game_core.Point, game_core.Vector, game_core.Vector, game_core.Vector) -> None
        self.pos = pos
        self.pos_vector = pos_vector or game_core.Vector()
        self.normal = normal
        self.normal_vector = normal_vector or game_core.Vector()


class LodTestItem(game_core.TreeNode):
    def get_item_value(self):
        return self.get_value()[0]

    def get_vertexes(self):
        return self.get_value()[1]

    def get_gl_vertex_array(self):
        return self.get_value()[2]

    def set_item_value(self, value):
        self.get_value()[0] = value

    def set_vertexes(self, vertexes):
        self.get_value()[1] = vertexes

    def set_gl_vertex_array(self, vertex_array_object):
        self.get_value()[2] = vertex_array_object

    def init(self):
        # TODO: figure out a better way to set values and init
        # self.set_value([None, None, None])
        if self.is_branch():
            self.init_branch_vertexes()
        elif self.get_item_value() is None:
            return
        else:
            self.init_leaf_vertexes()

    def init_leaf_vertexes(self):
        # initialize vert list with default values from smooth cube
        self.set_vertexes(tuple(
            TransitionVertex(
                pos=self.get_origin() + game_core.Vector(
                    smooth_cube.VERTICES[i * 3],
                    smooth_cube.VERTICES[i * 3 + 1],
                    smooth_cube.VERTICES[i * 3 + 2],
                ) * self.get_size(),
                normal=game_core.Vector(
                    smooth_cube.NORMALS[i * 3],
                    smooth_cube.NORMALS[i * 3 + 1],
                    smooth_cube.NORMALS[i * 3 + 2],
                ),
            )
            for i in range(8)
        ))

    def init_branch_vertexes(self):
        # initialize verts based on children's verts
        vertexes = []  # type: List[TransitionVertex]
        children = self.get_children()
        vert_types = []  # type: List[int]
        SAME_AS_CHILD = 0
        SAME_AS_CHILD_NEIGHBOR = 1
        SAME_AS_ORIGIN = 2
        for i, child in enumerate(children):
            # TODO: copy values instead of referencing
            if child.get_value() is not None and child.get_item_value() is not None:
                pos = child.get_vertexes()[i].pos
                normal = child.get_vertexes()[i].normal
                vert_types.append(SAME_AS_CHILD)
            else:
                for neighbor in self.tree.neighbor_indexes[i]:
                    if children[neighbor].get_value() is not None and children[neighbor].get_item_value() is not None:
                        pos = children[neighbor].get_vertexes()[i].pos
                        normal = children[neighbor].get_vertexes()[i].normal
                        vert_types.append(SAME_AS_CHILD_NEIGHBOR)
                        break
                else:
                    pos = self.get_origin()
                    vert_types.append(SAME_AS_ORIGIN)
                    # TODO: figure out proper normals
                    normal = game_core.Vector(
                        smooth_cube.NORMALS[i * 3],
                        smooth_cube.NORMALS[i * 3 + 1],
                        smooth_cube.NORMALS[i * 3 + 2],
                    )
            vertexes.append(TransitionVertex(pos=pos, normal=normal))

        # update transition vectors for children's verts
        for i, child in enumerate(children):
            if child.get_value() is None or child.get_item_value() is None:
                continue
            for j, vertex in enumerate(child.get_vertexes()):
                vertex.pos_vector = vertexes[j].pos - vertex.pos
                vertex.normal_vector = vertexes[j].normal - vertex.normal
        self.set_vertexes(tuple(vertexes))

    def init_gl_vertex_array(self):
        vertex_array = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(vertex_array)
        self.set_gl_vertex_array(vertex_array)

        vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        vertexes = self.get_vertexes()
        data = [v.pos[i] for v in vertexes for i in range(3)]
        data += [v.normal[i] for v in vertexes for i in range(3)]
        data += [v.pos_vector[i] for v in vertexes for i in range(3)]
        data += [v.normal_vector[i] for v in vertexes for i in range(3)]

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
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(vertexes)*3*FLOAT_SIZE))
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(vertexes)*3*2*FLOAT_SIZE))
        GL.glVertexAttribPointer(3, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(vertexes)*3*3*FLOAT_SIZE))

        index_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, index_buffer)
        array_type = (GL.GLuint*len(smooth_cube.INDICES))
        GL.glBufferData(
                GL.GL_ELEMENT_ARRAY_BUFFER,
                len(smooth_cube.INDICES)*FLOAT_SIZE,
                array_type(*smooth_cube.INDICES),
                GL.GL_STATIC_DRAW
        )

        GL.glBindVertexArray(0)

    def draw(self, window):
        # type: (Window) -> None
        if self.is_branch():
            camera_world_position = self.camera._pos
            distance_to_camera = 
            transition_end_distance = self.get_depth() +
            radius = 
            if distance_to_camera + radius > transition_end_distance:
                for child in self.get_children();
                    child.draw(window)
                return

        gl_vertex_array = self.get_gl_vertex_array()
        if gl_vertex_array is None:
            return

        with window.shaders['lod_test_{}'.format(self.get_depth())]:
            GL.glBindVertexArray(gl_vertex_array)
            GL.glDrawElements(smooth_cube.DRAW_METHOD, len(smooth_cube.INDICES), GL.GL_UNSIGNED_INT, None)
            GL.glBindVertexArray(0)


class LodTestTree(game_core.Octree):

    def _create_node_proxy(self, data, parent=None, index=0):
        """
        Returns:
            TreeNode
        """
        return LodTestItem(data, tree=self, parent=parent, index=index)

    def init(self):
        height_map_path = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'resources', 'BritanniaHeightMap2.exr'))
        image_buf = OpenImageIO.ImageBuf(height_map_path, 0, 7)  # 8k image so miplevel 7 should be 64
        depth = 6
        assert 2 ** depth == image_buf.spec().width
        root = self.get_root()  # type: LodTestItem

        items = [root]
        items_by_depth = [list() for i in range(depth)]
        items_by_depth[0].append(root)
        while items:
            item = items.pop()
            item.set_value([None, None, None])

            bounds = item.get_bounds()
            bounds_min = bounds.min()
            bounds_max = bounds.max()
            region_of_interest = OpenImageIO.ROI(
                bounds_min.x, bounds_max.x + 1.0,
                bounds_min.z, bounds_max.z + 1.0,
                None, None,
                0, 1,
            )
            stats = OpenImageIO.ImageBufAlgo.computePixelStats(
                image_buf,
                region_of_interest,
                2,  # nthreads
            )
            if stats.max < (bounds_max.y / 64.0):
                continue
            elif stats.min > (bounds_min.y / 64.0):
                continue

            items_by_depth[item.get_depth()].append(item)
            if item.get_depth() < depth:
                item.split()
                items.extend(item.get_children())

        for depth_items in reversed(items_by_depth):
            for item in depth_items:
                if item.is_leaf():
                    item.set_child_value('foo')
                item.init()
                item.init_gl_vertex_array()

    def draw(self, window):
        # type: (Window) -> None
        root = self.get_root()  # type: LodTestItem
        root.draw(window)
        # if window.distance_to_camera > (window.transition_end_distance + window.transition_range + 2.0):
        #     root.draw(window)
        # else:
        #     for child in root.get_children():
        #         if child:
        #             child.draw(window)
        if window.level == 0:
            root.draw(window)
        else:
            for child in root.get_children():
                if child:
                    child.draw(window)


if __name__ == '__main__':
    Window().run()
