#! /usr/bin/python
import glfw
from OpenGL import GL

from typing import Dict, List, Tuple

import game_core
from game_core import FLOAT_SIZE
from tempest.data.lod_transition_proof_of_concept import smooth_cube
from tempest import shaders


class Camera(game_core.AbstractCamera):
    def __init__(self, position=None):
        super(Camera, self).__init__(position)
        self.acceleration_rate = 1.0

    def integrate(self, time, delta_time, window, mouse_movement):
        # type: (float, float, Window, Tuple[float, float]) -> None
        if mouse_movement[0]:
            print 'X: {}'.format(mouse_movement)
        if mouse_movement[1]:
            print 'Y: {}'.format(mouse_movement)

        # add mouse_move to rotation values
        #
        self._rotx += mouse_movement[1]
        self._rotx = self.clamp_angle(self._rotx)
        self._roty -= mouse_movement[0]
        ry = self._get_roty_matrix()
        rx = self._get_rotx_matrix()

        # add movement
        #
        translate = game_core.Vector()
        if glfw.KEY_W in window.pressed_keys:
            translate.z += self.acceleration_rate
        if glfw.KEY_S in window.pressed_keys:
            translate.z -= self.acceleration_rate
        if glfw.KEY_A in window.pressed_keys:
            translate.x += self.acceleration_rate
        if glfw.KEY_D in window.pressed_keys:
            translate.x -= self.acceleration_rate
        if glfw.KEY_SPACE in window.pressed_keys:
            translate.y += self.acceleration_rate
        if glfw.KEY_LEFT_SHIFT in window.pressed_keys:
            translate.y -= self.acceleration_rate
        translate *= delta_time
        translate *= ry
        self._pos += translate

        # resolve xform components to a full matrix
        #
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

    def init(self):
        super(Window, self).init()
        self.cube = game_core.Mesh(smooth_cube.VERTICES, smooth_cube.NORMALS, smooth_cube.INDICES, smooth_cube.DRAW_METHOD)
        self.shaders = shaders.init()
        self.camera = Camera([0, 0, 2])
        self.lod_tree = LodTestTree(size=2, max_depth=2)
        self.lod_tree.init()

    def reshape(self, w, h):
        super(Window, self).reshape(w, h)

        window_center = [w / 2, h / 2]
        glfw.set_cursor_pos(self.window, *window_center)

        self.camera.reshape(w, h)

        projection_matrix = self.camera.projection_matrix.tolist()
        for shader in self.shaders.itervalues():
            if 'cameraToClipMatrix' not in shader.uniforms:
                continue
            with shader:
                GL.glUniformMatrix4fv(
                    shader.uniforms['cameraToClipMatrix'],
                    1,
                    GL.GL_FALSE,
                    projection_matrix,
                )

    def get_mouse_movement(self):
        # type: () -> Tuple[float, float]
        window_size = glfw.get_framebuffer_size(self.window)
        window_center = [window_size[0] / 2, window_size[1] / 2]

        cursor_pos = glfw.get_cursor_pos(self.window)
        glfw.set_cursor_pos(self.window, *window_center)

        mouse_movement = (
            float(cursor_pos[0] - window_center[0]) / window_center[0],
            float(cursor_pos[1] - window_center[1]) / window_center[1],
        )
        return mouse_movement

    def integrate(self, t, delta_time):
        self.camera.integrate(t, delta_time, self, self.get_mouse_movement())

    def draw(self):
        i_cam_mat = self.camera.matrix.inverse().tolist()
        for shader in self.shaders.itervalues():
            if 'worldToCameraMatrix' not in shader.uniforms:
                continue
            with shader:
                GL.glUniformMatrix4fv(
                    shader.uniforms['worldToCameraMatrix'],
                    1,
                    GL.GL_FALSE,
                    i_cam_mat
                )

        light_dir = game_core.Vector(0.1, 1.0, 0.5)
        light_dir.normalize()
        distance_to_camera = (game_core.Point() * self.camera.matrix).distance(self.lod_tree.get_root().get_origin())

        with self.shaders['lod_test'] as shader:
            GL.glUniform4fv(shader.uniforms['dirToLight'], 1, list(light_dir))
            GL.glUniform1f(shader.uniforms['distanceToCamera'], distance_to_camera)
            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)
            self.lod_tree.draw(distance_to_camera)


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
        self.init_gl_vertex_array()

    def init_leaf_vertexes(self):
        # initialize vert list with default values from smooth cube
        self.set_vertexes(tuple(
            TransitionVertex(
                pos=game_core.Point(
                    smooth_cube.VERTICES[i * 3],
                    smooth_cube.VERTICES[i * 3 + 1],
                    smooth_cube.VERTICES[i * 3 + 2],
                ),
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
        for i, child in enumerate(children):
            # TODO: copy values instead of referencing
            if child.get_value() is not None and child.get_item_value() is not None:
                pos = child.get_vertexes()[i].pos
                normal = child.get_vertexes()[i].normal
            else:
                for neighbor in self.tree.neighbor_indexes[i]:
                    child = children[neighbor]
                    if child.get_value() is not None and child.get_item_value() is not None:
                        pos = child.get_vertexes()[i].pos
                        normal = child.get_vertexes()[i].normal
                        break
                else:
                    pos = self.get_origin()
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
                if i == j:
                    continue
                else:
                    vertex.pos_vector = vertexes[j].pos - vertex.pos
                    vertex.normal_vector = vertexes[j].normal - vertex.normal
                    if children[j]:
                        vertex.pos_vector *= 0.5
                        vertex.normal_vector *= 0.5
        self.set_vertexes(tuple(vertexes))

    def init_gl_vertex_array(self):
        vertex_array = GL.glGenVertexArrays(1)
        self.set_gl_vertex_array(vertex_array)
        vertexes = self.get_vertexes()
        data = [v.pos[i] for v in vertexes for i in range(3)]
        data += [v.normal[i] for v in vertexes for i in range(3)]
        data += [v.pos_vector[i] for v in vertexes for i in range(3)]
        data += [v.normal_vector[i] for v in vertexes for i in range(3)]

        GL.glBindVertexArray(vertex_array)
        vertex_buffer = GL.glGenBuffers(1)

        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
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
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(vertexes)*FLOAT_SIZE))
        GL.glVertexAttribPointer(2, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(vertexes)*2*FLOAT_SIZE))
        GL.glVertexAttribPointer(3, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(vertexes)*3*FLOAT_SIZE))

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

    def draw(self):
        gl_vertex_array = self.get_gl_vertex_array()
        if gl_vertex_array is None:
            return

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
        root = self.get_root()  # type: LodTestItem
        root.set_value([None, None, None])
        root.split()
        children = root.get_children()  # type: List[LodTestItem]
        for child in children:
            child.set_value([None, None, None])
        children_to_fill = (0b000, 0b111)
        for index in children_to_fill:
            child = children[index]
            child.set_item_value('foo')
            child.init()
        root.init()

    def draw(self, distance_to_camera):
        # type: (float) -> None
        root = self.get_root()  # type: LodTestItem
        if distance_to_camera > 4:
            root.draw()
        else:
            for child in root.get_children():
                if child:
                    child.draw()


def generate_scenarios():
    import inspect

    def _process_string(s, indent):
        # type: (str, int) -> str
        return '\n'.join([('    '*indent+line) for line in s.splitlines()])

    header_template = inspect.cleandoc('''
        # Scenario {scenario}:
        #
        #        {7}      {4}
        #                     ^
        #   {3}      {0}          y
        #                    z x >
        #        {6}      {5}   L
        #
        #   {2}      {1}
        #
    ''')
    coord_template = inspect.cleandoc('''
        (
            (..., ..., ...),
            (..., ..., ...),
            (..., ..., ...),
            (..., ..., ...),
            (..., ..., ...),
            (..., ..., ...),
            (..., ..., ...),
            (..., ..., ...),
        ),
    ''')
    lines = ['scenarios = [']
    for i in range(256):
        children_present = []
        child_bit = 0b00000001
        while child_bit != 0b100000000:
            children_present.append(bool(child_bit & i))
            child_bit = child_bit << 1

        header_values = ['x' if cp else '-' for cp in children_present]
        header = header_template.format(*header_values, scenario=i)

        if children_present.count(True) == 1:
            single_child_template = coord_template.replace('...', '0.0')
            coord_values = [single_child_template if cp else 'None,' for cp in children_present]
        else:
            coord_values = [coord_template if cp else 'None,' for cp in children_present]

        lines.append('')
        lines.extend(_process_string(header, indent=1).splitlines())
        lines.append('    (')
        lines.extend([_process_string(v, indent=2) for v in coord_values])
        lines.append('    ),')
    lines.append('')
    lines.append(']')

    print('\n'.join(lines))
    with open('/Users/tymonpitts/dev/game_test/python/tempest/data/lod_transition_proof_of_concept/generated_transitions.py', 'w') as handle:
        handle.write('\n'.join(lines))
    print('DONE')


if __name__ == '__main__':
    Window().run()
    # generate_scenarios()
