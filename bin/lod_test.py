#! /usr/bin/python
import glfw
from OpenGL import GL
from typing import Dict, Optional, Tuple

import game_core
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
        self.title = 'Window'
        self.cube = None  # type: game_core.Mesh
        
        self.shaders = None  # type: Dict[str, game_core.ShaderProgram]
        self.camera = None  # type: Camera

    def init(self):
        super(Window, self).init()
        self.cube = game_core.Mesh(smooth_cube.VERTICES, smooth_cube.NORMALS, smooth_cube.INDICES, smooth_cube.DRAW_METHOD)
        self.shaders = shaders.init()
        self.camera = Camera([0, 0, 2])

    def keyboard_event(self, key, scancode, action, mods):
        """
        Args:
            key (int): The keyboard key that was pressed or released.
            scancode (int): The system-specific scancode of the key.
            action (int): glfw.PRESS, glfw.RELEASE or glfw.REPEAT.
            mods (int): Bit field describing which modifier keys were held down.
        """
        super(Window, self).keyboard_event(key, scancode, action, mods)

    def mouse_button_event(self, button, action, mods):
        """Called when a mouse button is pressed or released

        :param int button: The pressed/released mouse button
        :param int action: glfw.PRESS or glfw.RELEASE
        :param int mods: Bit field describing which modifier keys were held down.
        """
        pass

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

        with self.shaders['skin'] as shader:
            light_dir = game_core.Vector(0.1, 1.0, 0.5)
            light_dir.normalize()
            GL.glUniform4fv(shader.uniforms['dirToLight'], 1, list(light_dir))

        with self.shaders['skin'] as shader:
            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.5, 0.5, 0.5, 1.0)
            self.cube.render()


class TransitionVertex(object):
    def __init__(self, pos, normal, pos_vector=None, normal_vector=None):
        # type: (game_core.Point, game_core.Vector, game_core.Vector, game_core.Vector) -> None
        self.pos = pos
        self.pos_vector = pos_vector or game_core.Vector()
        self.normal = normal
        self.normal_vector = normal_vector or game_core.Vector()


class LodTestItem(game_core.TreeNode):

    def __init__(self, data, tree, parent, index):
        """
        Args:
            data (Any): The data for this node.  This could be anything but
                it's worth noting that a branch node is denoted by having its
                data be a list of child data.
            tree (AbstractTree): The tree this node belongs to.
            parent (Union[TreeNode, None]):
            index (int): This node's index in its parent's list of children
        """
        # TODO: store verts/faces in tree data
        super(LodTestItem, self).__init__(data, tree, parent, index)
        self.vertices = None  # type: Optional[Tuple[TransitionVertex]]
        self.faces = None  # type: Optional[Tuple[int]]

    def init_vertices(self):
        # no data so clear vert/face lists and exit
        if not self._data:
            self.vertices = None
            self.faces = None
            return

        # initialize vert/face lists with default values
        self.vertices = tuple(
            TransitionVertex(
                pos=game_core.Point(*smooth_cube.VERTICES[i]),
                normal=game_core.Vector(*smooth_cube.NORMALS[i]),
            )
            for i in range(8)
        )
        self.faces = smooth_cube.INDICES

        # if we're a leaf node then early exit. Transition vectors will be
        # computed when initializing parent verts
        if self.is_leaf():
            return

        # we're a branch. initialize verts based on children
        children = self.get_children()
        for i, child in enumerate(children):
            if child:
                self.vertices[i].pos = child.vertices[i].pos
                self.vertices[i].normal = child.vertices[i].normal
            else:
                for neighbor in self.tree.NEIGHBORS[i]:
                    child = children[neighbor]
                    if child:
                        self.vertices[i].pos = child.vertices[i].pos
                        self.vertices[i].normal = child.vertices[i].normal
                        break
                else:
                    self.vertices[i].pos = self.get_origin()
                    self.vertices[i].normal = ...

        # update transition vectors for children's verts
        for i, child in enumerate(children):
            if not child:
                continue
            for j, vertex in enumerate(child.vertices):
                if i == j:
                    continue
                else:
                    vertex.pos_vector = self.vertices[j].pos - vertex.pos
                    vertex.normal_vector = self.vertices[j].normal - vertex.normal
                    if children[j]:
                        vertex.pos_vector *= 0.5
                        vertex.normal_vector *= 0.5


class LodTestTree(game_core.Octree):

    def _create_node_proxy(self, data, parent=None, index=0):
        """
        Returns:
            TreeNode
        """
        return LodTestItem(data, tree=self, parent=parent, index=index)


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
