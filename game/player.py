#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math

import numpy
import glfw
from OpenGL import GL

from .. import core

#============================================================================#
#=================================================================== CLASS ==#
class Player(core.AbstractCamera):
    def __init__(self, *args, **kwargs):
        super(Player, self).__init__(*args, **kwargs)

        self.eye_level = 1.7
        # self.height = 1.75
        # self.width = 0.5
        # self.depth = 0.25
        self.bbox = core.BoundingBox([-0.25, 0.0, -0.25], [0.25, 1.75, 0.25])

        # self.walking_speed = 1.4
        self.walking_speed = 3.0
        # self.walking_acceleration = 0.2 # number of secs to reach top speed
        self.velocity = core.Vector()
        self._grounded = True

    def world(self):
        from .. import GAME
        return GAME.world

    def render(self):
        bbox = self._get_bbox_at_pos(self._pos)
        mat = core.Matrix()
        center = bbox.center()
        for i in xrange(3):
            mat[i,i] = bbox.get_dimension(i)
            mat[3,i] = center[i]

        with self.game().shaders['skin'] as shader:
            GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat.tolist())
            self.game().cube.render()

    def camera_matrix(self):
        offset = core.Matrix()
        offset.rotateX(45.0)
        offset[3,1]=5.0
        offset[3,2]=-5.0
        return offset * self.matrix

    def update(self):
        # add mouse_move to rotation values
        # 
        self._rotx += self.game().mouse_movement[1]
        self._rotx = self.clamp_angle(self._rotx)
        self._roty -= self.game().mouse_movement[0]
        ry = self._get_roty_matrix()
        rx = self._get_rotx_matrix()

        # convert input to an acceleration vector
        #
        if self._grounded:
            acceleration = self._update_for_ground()
        else:
            acceleration = self._update_for_air()

        # if we have acceleration, perform collision detection 
        # and adjust the acceleration vector accordingly
        #
        if acceleration.length():
            acceleration *= ry
            components = [0,1,2]
            start_pos = self._pos
            solution, solution_component = self.solve_collision(start_pos, acceleration)
            while solution_component is not None:
                try:
                    components.remove(solution_component)
                except ValueError:
                    print 'self._pos:', self._pos
                    print 'components:', components
                    print 'start_pos:', start_pos
                    print 'acceleration:', acceleration
                    print 'solution_component:', solution_component
                    print 'solution:', solution
                    raise
                start_pos = start_pos + solution
                acceleration = acceleration - solution
                acceleration[solution_component] = 0.0
                solution, solution_component = self.solve_collision(start_pos, acceleration)
            self._pos = start_pos + solution

            # determine if we are grounded or in the air
            #
            bbox = self._get_bbox_at_pos(self._pos)
            blocks = self.game().world.get_blocks(bbox, inclusive=True)
            self._grounded = bool(blocks)

        # resolve xform components to a full matrix
        #
        self.matrix = rx * ry
        for i in xrange(3):
            self.matrix[3,i] = self._pos[i]

        if ' ' in self.game().pressed_keys:
            print 'pos:', self._pos

    def solve_collision(self, start_pos, acceleration):
        pos1 = start_pos
        pos2 = start_pos + acceleration

        # detect collisions
        #
        bbox1 = self._get_bbox_at_pos(pos1)
        bbox2 = self._get_bbox_at_pos(pos2)
        bbox = core.BoundingBox()
        bbox.bbox_expand(bbox1)
        bbox.bbox_expand(bbox2)

        blocks = self.game().world.get_blocks(bbox)

        # solve collisions
        #
        t = 1.0
        component = None
        for block in blocks:
            this_t, this_component = block.solve_collision(bbox1, acceleration)
            if this_t < t:
                t = this_t
                component = this_component

        # if collision_boxes:
        #     print '='*78
        #     print 'pos:', self._pos
        #     print 'acceleration:', acceleration
        #     print 'collider:', bbox
        #     print 'collisions:'
        #     for box, block_bbox in collision_boxes:
        #         print '|   %s %s' % (box, block_bbox)
        #     print 'solution t:', t

        solution = acceleration * t

        return solution, component

    def _get_bbox_at_pos(self, pos):
        bbox = self.bbox.copy()
        bbox._min += pos
        bbox._max += pos
        return bbox

    def _update_for_ground(self):
        trans = core.Vector()
        if 'W' in self.game().pressed_keys:
            trans.z += 1.0
        if 'S' in self.game().pressed_keys:
            trans.z -= 1.0
        if 'A' in self.game().pressed_keys:
            trans.x += 1.0
        if 'D' in self.game().pressed_keys:
            trans.x -= 1.0
        trans.normalize()
        trans *= self.walking_speed * self.game().elapsed_time
        return trans

    def _update_for_air(self):
        trans = core.Vector()
        if 'W' in self.game().pressed_keys:
            trans.z += 1.0
        if 'S' in self.game().pressed_keys:
            trans.z -= 1.0
        if 'A' in self.game().pressed_keys:
            trans.x += 1.0
        if 'D' in self.game().pressed_keys:
            trans.x -= 1.0
        trans.normalize()
        trans *= self.walking_speed * self.game().elapsed_time
        trans.y -= 9.81 * self.game().elapsed_time
        return trans



    #     # get a before and after position
    #     #
    #     before = self._pos.copy()
    #     after = before + self.acceleration

    #     # check that the requested movement is valid
    #     #
    #     bbox = self.bbox.copy()
    #     bbox._min += after
    #     bbox._max += after
    #     collision = self.world().get_collision(bbox)
    #     if collision:
    #         t = self.acceleration.magnitude()
    #         for i in xrange(3):
    #             component = collision.get_dimension(i) / 2
    #             component += bbox.get_dimension(i) / 2
    #             if self.acceleration[i] < 0:
    #                 component = -component
    #             this_t = (component - before[i]) / after[i]
    #             t = min(t, this_t)
    #         acceleration = self.acceleration.normal() * t
    #         after = self._pos + acceleration

    #     self._pos = after

    # def handle_input(self, pressed_keys, mouse_move):
    #     # add mouse_move to rotation values
    #     # 
    #     self._rotx += mouse_move[1]
    #     self._rotx = self.clamp_angle(self._rotx)
    #     self._roty -= mouse_move[0]

    #     # convert pressed keys into a movement direction
    #     #
    #     trans = core.Vector()
    #     if 'W' in pressed_keys:
    #         trans.z += 1.0
    #     if 'S' in pressed_keys:
    #         trans.z -= 1.0
    #     if 'A' in pressed_keys:
    #         trans.x += 1.0
    #     if 'D' in pressed_keys:
    #         trans.x -= 1.0
    #     # if ' ' in pressed_keys:
    #     #     trans.y += self.movement_speed

    #     # make the length of movement vector equal to the movement speed
    #     #
    #     trans.normalize()
    #     trans *= self.movement_speed
    #     if glfw.KEY_LSHIFT in pressed_keys:
    #         trans *= 0.1

    #     # rotate the movement vector relative to 
    #     # the current facing direction
    #     #
    #     r_sy = math.sin(self._roty)
    #     r_cy = math.cos(self._roty)
    #     ry = core.Matrix()
    #     ry[0,0] = r_cy
    #     ry[0,2] = -r_sy
    #     ry[2,0] = r_sy
    #     ry[2,2] = r_cy

    #     trans = trans * ry

    #     # add the movement direction to the acceleration for this frame
    #     #
    #     self.acceleration += trans

    #     # self.last_movement = trans
    #     # self._trans += trans

    #     # self.matrix = rx * ry
    #     # for i in xrange(3):
    #     #     self.matrix[3,i] = self._trans[i]

