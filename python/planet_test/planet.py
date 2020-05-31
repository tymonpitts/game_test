from __future__ import absolute_import, division, print_function

import math
from typing import TYPE_CHECKING

from OpenGL import GL
import astropy_healpix
import trimesh
import game_core

from .planet_top_chunk import PlanetTopChunk

if TYPE_CHECKING:
    # guarded to prevent circular dependencies
    from .window import Window


class Planet(object):
    def __init__(self, circumference, chunk_height):
        # type: (float, float) -> None
        # # Earth's Mesosphere (atmosphere) is ~100km and the Lithosphere (crust) is ~100km thick
        # self.chunk_height = 200000.0
        # self.circumference = 40075017.0
        self.circumference = circumference
        self.chunk_height = chunk_height
        self.radius = self.circumference / (2.0 * math.pi)
        self.chunks = [PlanetTopChunk(self, index) for index in range(astropy_healpix.nside_to_npix(1))]
        self.mesh = None
        self.gl_vertex_array = None
        self.gl_vertex_array_num_indexes = None
        self.gl_point_vertex_array = None
        self.gl_point_vertex_array_num_vertexes = None

        # # Earth's Mesosphere (atmosphere) is ~100km and the Lithosphere
        # # (crust) is ~100km thick so if our chunk sizes are 256km (needs
        # # to be a power of 2) then that should include everything
        # self.chunk_size = 256000.0  # meters  # TODO: this is wrong...
        # self.chunk_min_size = 0.25
        #
        # # Earth's radius (excluding atmosphere) is ~6,370km so if we
        # # use 24 chunks we'll be at 6144km and we'll be divisible by
        # # 4 so we can have a sphere made up of cube chunks
        # self.radius_in_chunks = 24
        # self.radius = self.chunk_size * self.radius_in_chunks
        # self.chunk_angle_size = 360.0 / self.radius_in_chunks
        #
        # # create chunks to represent each face of the planet's "cube"
        # # which we'll wrap together to form the quad sphere
        # chunks_per_face = self.radius_in_chunks // 4
        #
        # self.chunks = []  # type: List[List[List[PlanetTopChunk]]]
        # face_edge_polar_angle = 45.0
        # for face_index in range(4):
        #     self.chunks.append([])
        #     polar_angle = face_edge_polar_angle + self.chunk_angle_size
        #     for x_index in range(chunks_per_face):
        #         azimuthal_angle = -45.0 + self.chunk_angle_size
        #         self.chunks[face_index].append([])
        #         for y_index in range(chunks_per_face):
        #             self.chunks[face_index][x_index].append(PlanetTopChunk(self, polar_angle, azimuthal_angle))
        #             azimuthal_angle += self.chunk_angle_size
        #         polar_angle += self.chunk_angle_size
        #     face_edge_polar_angle += self.chunk_angle_size * chunks_per_face
        #
        # top_face_index = 4
        # self.chunks.append([])
        # polar_angle = -45.0 + self.chunk_angle_size
        # for x_index in range(chunks_per_face):
        #     azimuthal_angle = -45.0 + self.chunk_angle_size
        #     self.chunks[top_face_index].append([])
        #     for y_index in range(chunks_per_face):
        #         self.chunks[top_face_index][x_index].append(PlanetTopChunk(self, polar_angle, azimuthal_angle))
        #         azimuthal_angle += self.chunk_angle_size
        #     polar_angle += self.chunk_angle_size
        # face_edge_polar_angle += self.chunk_angle_size * chunks_per_face
        #
        # self.chunks = [
        #     [
        #         PlanetTopChunk(self)
        #         for chunk in range(chunks_per_face * chunks_per_face)
        #     ]
        #     for face in range(6)
        # ]

    def init(self):
        # TODO: use marching cubes
        #       - scikit has an implementation that I should look into but need to check what `volume=(M, N, P) array` means

        for chunk in self.chunks:
            chunk.compute_vertexes()

        # create a Cuboctahedron using the centers of each chunk as the vertices
        # TODO: might want to look into Dymaxion maps
        vertexes = [chunk.vertex[:3] for chunk in self.chunks]
        faces = []
        for chunk in self.chunks:
            neighbor_indexes = astropy_healpix.neighbours(chunk.index, 1, order='nested')
            faces.append([chunk.index, neighbor_indexes[0], neighbor_indexes[2]])
            if neighbor_indexes[1] == -1:
                # add caps
                if chunk.index == 0:
                    faces.append([chunk.index, neighbor_indexes[2], neighbor_indexes[4]])
                    faces.append(neighbor_indexes[2:5])
                elif chunk.index == 8:
                    faces.append([chunk.index, neighbor_indexes[6], neighbor_indexes[0]])
                    faces.append([neighbor_indexes[6], neighbor_indexes[7], neighbor_indexes[0]])
            else:
                faces.append(neighbor_indexes[:3])
        self.mesh = trimesh.Trimesh(
            vertices=vertexes,
            faces=faces,
            process=False,  # otherwise verts are re-ordered
            validate=False,  # otherwise verts are re-ordered
        )

        positions_data = [num for vertex in self.mesh.vertices for num in vertex]
        normals_data = [num for normal in self.mesh.vertex_normals for num in normal]
        indexes_data = [num for face in self.mesh.faces for num in face]

        self.gl_vertex_array_num_indexes = len(indexes_data)
        if self.gl_vertex_array is None:
            self.gl_vertex_array = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.gl_vertex_array)
        vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        data = positions_data + normals_data
        array_type = (GL.GLfloat*len(data))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(data)*game_core.FLOAT_SIZE,
            array_type(*data),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glEnableVertexAttribArray(1)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)
        GL.glVertexAttribPointer(1, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, GL.GLvoidp(len(positions_data)*game_core.FLOAT_SIZE))

        index_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ELEMENT_ARRAY_BUFFER, index_buffer)
        array_type = (GL.GLuint*len(indexes_data))
        GL.glBufferData(
            GL.GL_ELEMENT_ARRAY_BUFFER,
            len(indexes_data)*game_core.FLOAT_SIZE,
            array_type(*indexes_data),
            GL.GL_STATIC_DRAW
        )

        GL.glEnable(GL.GL_PROGRAM_POINT_SIZE)
        self.gl_point_vertex_array_num_vertexes = len(self.mesh.vertices)
        if self.gl_point_vertex_array is None:
            self.gl_point_vertex_array = GL.glGenVertexArrays(1)
        GL.glBindVertexArray(self.gl_point_vertex_array)
        vertex_buffer = GL.glGenBuffers(1)
        GL.glBindBuffer(GL.GL_ARRAY_BUFFER, vertex_buffer)
        data = positions_data
        array_type = (GL.GLfloat*len(data))
        GL.glBufferData(
            GL.GL_ARRAY_BUFFER,
            len(data)*game_core.FLOAT_SIZE,
            array_type(*data),
            GL.GL_STATIC_DRAW
        )
        GL.glEnableVertexAttribArray(0)
        GL.glVertexAttribPointer(0, 3, GL.GL_FLOAT, GL.GL_FALSE, 0, None)

        GL.glBindVertexArray(0)

    def draw(self, window):
        # type: (Window) -> None
        # draw faces with constant color
        GL.glBindVertexArray(self.gl_vertex_array)
        with game_core.shaders.CONSTANT as shader:
            shader.set_uniform('color', 1, 1, 1, 1)
            GL.glDrawElements(GL.GL_TRIANGLES, self.gl_vertex_array_num_indexes, GL.GL_UNSIGNED_INT, None)

        # draw edges
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_LINE)
        with game_core.shaders.CONSTANT:
            shader.set_uniform('color', 0, 0, 0, 1)
            GL.glDrawElements(GL.GL_TRIANGLES, self.gl_vertex_array_num_indexes, GL.GL_UNSIGNED_INT, None)
        GL.glPolygonMode(GL.GL_FRONT_AND_BACK, GL.GL_FILL)

        # draw points
        with game_core.shaders.POINT:
            GL.glBindVertexArray(self.gl_point_vertex_array)
            GL.glDrawArrays(GL.GL_POINTS, 0, self.gl_point_vertex_array_num_vertexes)
            GL.glBindVertexArray(0)

        # draw vert indexes
        for i, vert in enumerate(self.mesh.vertices):
            window.render_text_3d(str(i), pos=game_core.Point(*vert))

        GL.glBindVertexArray(0)
