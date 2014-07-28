#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math

from OpenGL import GL
import glfw

from ... import core
from ... import data

#============================================================================#
#=================================================================== CLASS ==#
class Camera(core.AbstractCamera):
    def handle_input(self, game):
        if '[' in game.pressed_keys or ']' in game.pressed_keys:
            return

        self.movement_speed = 0.1

        trans = core.Point()
        if 'W' in game.pressed_keys:
            trans.z += self.movement_speed
        if 'S' in game.pressed_keys:
            trans.z -= self.movement_speed
        if 'A' in game.pressed_keys:
            trans.x += self.movement_speed
        if 'D' in game.pressed_keys:
            trans.x -= self.movement_speed
        if ' ' in game.pressed_keys:
            trans.y += self.movement_speed
        if glfw.KEY_LSHIFT in game.pressed_keys:
            trans.y -= self.movement_speed

        # convert mouse movement into rotation matrices
        # 
        self._rotx += game.mouse_movement[1]
        self._rotx = self.clamp_angle(self._rotx)
        r_sx = math.sin(self._rotx)
        r_cx = math.cos(self._rotx)
        rx = core.Matrix()
        rx[1,1] = r_cx
        rx[1,2] = r_sx
        rx[2,1] = -r_sx
        rx[2,2] = r_cx

        self._roty -= game.mouse_movement[0]
        r_sy = math.sin(self._roty)
        r_cy = math.cos(self._roty)
        ry = core.Matrix()
        ry[0,0] = r_cy
        ry[0,2] = -r_sy
        ry[2,0] = r_sy
        ry[2,2] = r_cy

        trans = trans * ry
        self._pos += trans
        self.matrix = rx * ry
        for i in xrange(3):
            self.matrix[3,i] = self._pos[i]

class Collider(object):
    def __init__(self):
        self.bbox = core.BoundingBox([-0.25, 0.0, -0.25], [0.25, 1.75, 0.25])
        self._pos1 = core.Point()
        self._pos2 = core.Point()
        self._pos3 = core.Point()

        self._collision_box = None

        self.box_solid = core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, data.cube.DRAW_METHOD)
        self.box_outline = core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, GL.GL_LINE_LOOP)

    def handle_input(self, game):
        if '[' not in game.pressed_keys and ']' not in game.pressed_keys:
            return

        trans = core.Vector()
        if 'W' in game.pressed_keys:
            trans.z += 1.0
        if 'S' in game.pressed_keys:
            trans.z -= 1.0
        if 'A' in game.pressed_keys:
            trans.x += 1.0
        if 'D' in game.pressed_keys:
            trans.x -= 1.0
        if ' ' in game.pressed_keys:
            trans.y += 1.0
        if glfw.KEY_LSHIFT in game.pressed_keys:
            trans.y -= 1.0
        trans.normalize()
        trans *= 0.1

        if '[' in game.pressed_keys:
            self._pos1 += trans
        if ']' in game.pressed_keys:
            self._pos2 += trans

        # detect collision
        #
        bbox1 = self.get_bbox(self._pos1)
        bbox2 = self.get_bbox(self._pos2)
        bbox = core.BoundingBox()
        bbox.bbox_expand(bbox1)
        bbox.bbox_expand(bbox2)

        self._collision_box = game.world.bbox.intersection(bbox)
        if not self._collision_box:
            self._pos3 = self._pos2
            return

        # get a before and after position
        #
        acceleration = self._pos2 - self._pos1
        before = bbox1.center()
        after = before + acceleration
        center = self._collision_box.center()

        expanded_collision_bbox = self._collision_box.copy()
        dimensions = core.Vector([self.bbox.get_dimension(i) / 2.0 for i in xrange(3)])
        expanded_collision_bbox._min -= dimensions
        expanded_collision_bbox._max += dimensions

        # check that the requested movement is valid
        #
        t = 1.0
        other_indices = [(1,2), (0,2), (0,1)]
        for i, others in enumerate(other_indices):
            if acceleration[i] == 0:
                continue

            if before[i] < self._collision_box._min[i]:
                component = self._collision_box._min[i]
                component -= self.bbox.get_dimension(i) / 2
            elif before[i] > self._collision_box._max[i]:
                component = self._collision_box._max[i]
                component += self.bbox.get_dimension(i) / 2
            else:
                continue

            this_t = (component - before[i]) / acceleration[i]
            this_accel = acceleration * this_t
            this_pos = before + this_accel
            invalid = False
            for other in others:
                if this_pos[other] < expanded_collision_bbox._min[other]:
                    invalid = True
                    break
                if this_pos[other] > expanded_collision_bbox._max[other]:
                    invalid = True
                    break
            if invalid:
                continue

            t = min(t, this_t)
        acceleration *= t
        self._pos3 = core.Point(self._pos1 + acceleration)

    def get_bbox(self, pos):
        bbox = self.bbox.copy()
        bbox._min += pos
        bbox._max += pos
        return bbox

    def get_mat(self, bbox):
        mat = core.Matrix()
        center = bbox.center()
        for i in xrange(3):
            mat[i,i] = bbox.get_dimension(i)
            mat[3,i] = center[i]
        return mat

    def render(self, game):
        mat1 = self.get_mat(self.get_bbox(self._pos1))
        mat2 = self.get_mat(self.get_bbox(self._pos2))
        mat3 = self.get_mat(self.get_bbox(self._pos3))

        with game.shaders['constant'] as shader:
            GL.glUniform4f(shader.uniforms['color'], 0.0, 1.0, 0.0, 1.0)
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat1.tolist())
            self.box_outline.render()

            GL.glUniform4f(shader.uniforms['color'], 1.0, 0.0, 0.0, 1.0)
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat2.tolist())
            self.box_outline.render()

        with game.shaders['cube'] as shader:
            GL.glUniform4f(shader.uniforms['diffuseColor'], 0.0, 0.0, 1.0, 1.0)
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat3.tolist())
            self.box_solid.render()

        if self._collision_box:
            mat = self.get_mat(self._collision_box)
            with game.shaders['constant'] as shader:
                GL.glUniform4f(shader.uniforms['color'], 0.9, 0.9, 0.0, 1.0)
                GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat.tolist())
                self.box_outline.render()

class World(object):
    def __init__(self):
        self.bbox = core.BoundingBox([-2,-2,-2],[2,2,2])
        self.box_outline = core.Mesh(data.cube.VERTICES, data.cube.NORMALS, data.cube.INDICES, GL.GL_LINE_LOOP)

    def render(self, game):
        mat = core.Matrix()
        for i in xrange(3):
            mat[i,i] = self.bbox.get_dimension(i)

        with game.shaders['constant'] as shader:
            GL.glUniform4f(shader.uniforms['color'], 0.9, 0.9, 0.9, 1.0)
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat.tolist())
            self.box_outline.render()

