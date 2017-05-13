#============================================================================#
#================================================================= IMPORTS ==#

from OpenGL import GL

import game_core
from . import Game

#============================================================================#
#=================================================================== CLASS ==#
class Player(game_core.AbstractCamera):
    def __init__(self, position):
        super(Player, self).__init__(position)
        self.mass = 65.0 # kilograms

        self.eye_level = 1.7
        # self.height = 1.75
        # self.width = 0.5
        # self.depth = 0.25
        self.bbox = game_core.BoundingBox([-0.25, 0.0, -0.25], [0.25, 1.75, 0.25])

        self.max_walking_speed = 3.0 # meters per second
        self.walking_force = self.mass * 2.0  # F = mass * acceleration (meters per second per second)
        self.jump_force = self.mass * 60.0 # F = mass * acceleration; average human a=30.0

        self.velocity = game_core.Vector()
        self._grounded = True

    def render(self):
        bbox = self._get_bbox_at_pos(self._pos)
        mat = game_core.Matrix()
        center = bbox.center()
        for i in xrange(3):
            mat[i,i] = bbox.get_dimension(i)
            mat[3,i] = center[i]

        with Game.INSTANCE.shaders['skin'] as shader:
            GL.glUniform4f(shader.uniforms['diffuseColor'], 1.0, 0.0, 0.0, 1.0)
            GL.glUniformMatrix4fv(shader.uniforms['modelToWorldMatrix'], 1, GL.GL_FALSE, mat.tolist())
            Game.INSTANCE.cube.render()

    def camera_matrix(self):
        offset = game_core.Matrix()
        offset.rotateX(45.0)
        offset[3,1]=5.0
        offset[3,2]=-5.0
        return offset * self.matrix

    def update(self, time, delta_time):
        # add mouse_move to rotation values
        # 
        self._rotx += Game.INSTANCE.mouse_movement[1]
        self._rotx = self.clamp_angle(self._rotx)
        self._roty -= Game.INSTANCE.mouse_movement[0]
        ry = self._get_roty_matrix()
        rx = self._get_rotx_matrix()

        # convert input to an acceleration vector
        #
        if self._grounded:
            acceleration = self._get_acceleration_on_ground(ry)
        else:
            acceleration = self._get_acceleration_in_air(ry)
        velocity = self.velocity + (acceleration * delta_time / 2.0)

        # clamp horizontal velocity to max_walking_speed
        #
        velocity_length = velocity.length()
        if velocity_length:
            h_velocity = velocity.copy()
            h_velocity[1] = 0.0
            h_velocity_length = h_velocity.length()
            max_walking_speed = self.max_walking_speed / delta_time
            if h_velocity_length > max_walking_speed:
                h_velocity_length = max_walking_speed
                h_velocity.normalize()
                h_velocity *= h_velocity_length
                velocity = Vector(h_velocity[0], velocity[1], h_velocity[2])

        # if we have velocity, perform collision detection 
        # and adjust the velocity vector accordingly
        #
        velocity_length = velocity.length()
        if velocity_length:
            start_pos = self._pos
            first_loop = True
            colliding_components = []

            # get colliding blocks
            #
            bbox1 = self._get_bbox_at_pos(start_pos)
            bbox2 = self._get_bbox_at_pos(start_pos + velocity)
            bbox = game_core.BoundingBox()
            bbox.bbox_expand(bbox1)
            bbox.bbox_expand(bbox2)
            blocks = Game.INSTANCE.world.get_blocks(bbox)

            count = 0
            while blocks and (first_loop or solution_component is not None):
                first_loop = False
                if count > 3:
                    raise Exception('infinite collision loop')
                count += 1

                # solve for collisions
                #
                solution_t, solution_component = self.solve_collision(start_pos, velocity, blocks)
                if solution_component is None: # no collisions
                    break
                colliding_components.append(solution_component)

                # prep the start position for another collision test by 
                # moving it to the last point of collision
                #
                start_pos = start_pos + (velocity * solution_t)

                # calculate the remaining velocity
                # 
                velocity_length -= (velocity_length * solution_t)
                velocity = velocity.normal() * velocity_length
                velocity[solution_component] = 0.0
                velocity_length = velocity.length()

            # set the new position
            #
            previous_pos = self._pos.copy()
            self._pos = start_pos + velocity
            self._pos.round()
            self.velocity = self._pos - previous_pos
            for component in colliding_components:
                self.velocity[component] = 0.0

            # determine if we are grounded or in the air
            #
            bbox = self._get_bbox_at_pos(self._pos)
            self._grounded = Game.INSTANCE.world.is_grounded(bbox)

        # resolve xform components to a full matrix
        #
        self.matrix = rx * ry
        for i in xrange(3):
            self.matrix[3,i] = self._pos[i]

        if 'P' in Game.INSTANCE.pressed_keys:
            print 'pos:', self._pos

    def solve_collision(self, start_pos=None, velocity=None, blocks=None):
        if start_pos is None:
            start_pos = self._pos
        if velocity is None:
            velocity = game_core.Vector()

        bbox1 = self._get_bbox_at_pos(start_pos)
        if blocks is None:
            pos2 = start_pos + velocity
            bbox2 = self._get_bbox_at_pos(pos2)
            bbox = game_core.BoundingBox()
            bbox.bbox_expand(bbox1)
            bbox.bbox_expand(bbox2)
            blocks = Game.INSTANCE.world.get_blocks(bbox)

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

    def _get_acceleration_on_ground(self, ry):
        # static_friction_coefficient = 1.0
        # kinetic_friction_coefficient = 0.8
        # friction_normal_force = self.mass * 9.81
        # velocity_length = self.velocity.length()
        # if not velocity_length:
        #     max_frictional_force = static_friction_coefficient * friction_normal_force
        # else:
        #     max_frictional_force = kinetic_friction_coefficient * friction_normal_force

        force = game_core.Vector()
        if 'W' in Game.INSTANCE.pressed_keys:
            force.z += 1.0
        if 'S' in Game.INSTANCE.pressed_keys:
            force.z -= 1.0
        if 'A' in Game.INSTANCE.pressed_keys:
            force.x += 1.0
        if 'D' in Game.INSTANCE.pressed_keys:
            force.x -= 1.0
        if force.length():
            force.normalize()
            force = force.normal() * self.walking_force
            force *= ry
        else:
            vel_force = self.velocity.length() * self.mass
            if not vel_force:
                pass
            elif vel_force < self.walking_force:
                force = self.velocity.normal() * -vel_force
            else:
                force = self.velocity.normal() * -(vel_force - self.walking_force)

        # add jumping force
        #
        if ' ' in Game.INSTANCE.pressed_keys:
            force.y += self.jump_force

        return (force / self.mass)

    def _get_acceleration_in_air(self, ry):
        force = game_core.Vector()
        if 'W' in Game.INSTANCE.pressed_keys:
            force.z += 1.0
        if 'S' in Game.INSTANCE.pressed_keys:
            force.z -= 1.0
        if 'A' in Game.INSTANCE.pressed_keys:
            force.x += 1.0
        if 'D' in Game.INSTANCE.pressed_keys:
            force.x -= 1.0
        force.normalize()
        force *= ry
        force *= self.walking_force # apply force magnitude
        force[1] -= self.mass * 9.81 # apply gravity
        return (force / self.mass) # a = f/m

