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

        self.max_walking_speed = 3.0
        self.walking_acceleration = 1.0
        # self.walking_acceleration = 0.2 # number of secs to reach top speed

        self.jump_force = 1.0

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
            acceleration = self._update_for_ground(ry)
        else:
            acceleration = self._update_for_air(ry)
        self.velocity = self.velocity + acceleration

        # if we have acceleration, perform collision detection 
        # and adjust the acceleration vector accordingly
        #
        velocity_length = self.velocity.length()
        if velocity_length:
            # print 'velocity:', self.velocity
            start_pos = self._pos
            first_loop = True
            count = 0
            while first_loop or solution_component is not None:
                first_loop = False
                if count > 3:
                    print count
                count += 1

                # solve for collisions
                #
                solution_t, solution_component = self.solve_collision(start_pos, self.velocity)
                if solution_component is None: # no collisions
                    break

                # prep the start position for another collision test by 
                # moving it to the last point of collision
                #
                start_pos = start_pos + (self.velocity * solution_t)

                # calculate the remaining velocity
                # 
                velocity_length -= (velocity_length * solution_t)
                self.velocity = self.velocity.normal() * velocity_length
                self.velocity[solution_component] = 0.0
                velocity_length = self.velocity.length()

            # set the new position
            #
            self._pos = start_pos + self.velocity

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

        if 'P' in self.game().pressed_keys:
            print 'pos:', self._pos

    def solve_collision(self, start_pos=None, velocity=None):
        if start_pos is None:
            start_pos = self._pos
        if velocity is None:
            velocity = core.Vector()

        pos1 = start_pos
        pos2 = start_pos + velocity

        # detect collisions
        #
        bbox1 = self._get_bbox_at_pos(pos1)
        bbox2 = self._get_bbox_at_pos(pos2)
        bbox = core.BoundingBox()
        bbox.bbox_expand(bbox1)
        bbox.bbox_expand(bbox2)

        blocks = self.game().world.get_blocks(bbox)

        # solve collisions for each block and use the solution with 
        # the smallest resulting velocity
        #
        t = 1.0
        component = None
        for block in blocks:
            this_t, this_component = block.solve_collision(bbox1, velocity)
            if this_t < t:
                t = this_t
                component = this_component

        return t, component

    def _get_bbox_at_pos(self, pos):
        bbox = self.bbox.copy()
        bbox._min += pos
        bbox._max += pos
        return bbox

    def _update_for_ground(self, ry):
        acceleration = core.Vector()
        if 'W' in self.game().pressed_keys:
            acceleration.z += 1.0
        if 'S' in self.game().pressed_keys:
            acceleration.z -= 1.0
        if 'A' in self.game().pressed_keys:
            acceleration.x += 1.0
        if 'D' in self.game().pressed_keys:
            acceleration.x -= 1.0
        acceleration.normalize()
        acceleration *= ry
        if acceleration.length():
            magnitude = self.walking_acceleration * self.game().elapsed_time
        else:
            magnitude = 0.0

        # limit the acceleration so that max speed is not exceeded
        #
        accelerating = (self.velocity.dot(acceleration) > 0)
        current_speed = self.velocity.length()
        if accelerating:
            new_speed = current_speed + magnitude
            if new_speed > self.max_walking_speed:
                # TODO: this logic is not complete.  Does not account for 
                # velocity already being higher than the max walking speed
                overshoot_amount = new_speed - self.max_walking_speed
                magnitude = magnitude - overshoot_amount

        # if we have no acceleration but we do have velocity, 
        # then we need to decelerate and the deceleration must 
        # not cause the velocity to invert it's direction (clamp to 0)
        #
        elif not magnitude and current_speed:
            acceleration = -self.velocity.normal()
            magnitude = self.walking_acceleration * self.game().elapsed_time
            # make sure this deceleration does not make velocity go negative
            if magnitude > current_speed:
                magnitude = current_speed

        # apply magnitude to acceleration vector
        #
        acceleration *= magnitude

        # add jumping force to the acceleration
        #
        if ' ' in self.game().pressed_keys:
            acceleration.y += self.jump_force
        return acceleration

    def _update_for_air(self, ry):
        acceleration = core.Vector()
        if 'W' in self.game().pressed_keys:
            acceleration.z += 1.0
        if 'S' in self.game().pressed_keys:
            acceleration.z -= 1.0
        if 'A' in self.game().pressed_keys:
            acceleration.x += 1.0
        if 'D' in self.game().pressed_keys:
            acceleration.x -= 1.0
        acceleration.normalize()
        acceleration *= ry
        magnitude = self.walking_acceleration * self.game().elapsed_time

        # apply magnitude to acceleration vector
        #
        acceleration *= magnitude

        # apply gravity
        #
        acceleration.y -= 9.81 * self.game().elapsed_time
        return acceleration



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
    #     acceleration = core.Vector()
    #     if 'W' in pressed_keys:
    #         acceleration.z += 1.0
    #     if 'S' in pressed_keys:
    #         acceleration.z -= 1.0
    #     if 'A' in pressed_keys:
    #         acceleration.x += 1.0
    #     if 'D' in pressed_keys:
    #         acceleration.x -= 1.0
    #     # if ' ' in pressed_keys:
    #     #     acceleration.y += self.movement_speed

    #     # make the length of movement vector equal to the movement speed
    #     #
    #     acceleration.normalize()
    #     acceleration *= self.movement_speed
    #     if glfw.KEY_LSHIFT in pressed_keys:
    #         acceleration *= 0.1

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

    #     acceleration = acceleration * ry

    #     # add the movement direction to the acceleration for this frame
    #     #
    #     self.acceleration += acceleration

    #     # self.last_movement = acceleration
    #     # self._trans += acceleration

    #     # self.matrix = rx * ry
    #     # for i in xrange(3):
    #     #     self.matrix[3,i] = self._trans[i]

