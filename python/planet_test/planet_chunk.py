from __future__ import absolute_import, division, print_function

import astropy_healpix
from typing import Optional, Tuple, TYPE_CHECKING
import trimesh

from . import utils


if TYPE_CHECKING:
    from .planet import Planet


class PlanetChunk(object):
    """ Octree structure where each level's data is a PlanetChunkData
    instance

    Child indices:

           2      3
                        ^
      6      7          y
                       z x >
           0      1   L

      4      5

    """
    # TODO: use __slots__ for performance optimization

    def __init__(self, parent, index):
        # type: (PlanetChunk, int) -> None
        self.parent = parent  # type: PlanetChunk
        self.index = index  # type: int
        # noinspection PyTypeChecker
        self.children = tuple([None] * 8)  # type: Tuple[Optional[PlanetChunk], Optional[PlanetChunk], Optional[PlanetChunk], Optional[PlanetChunk], Optional[PlanetChunk], Optional[PlanetChunk], Optional[PlanetChunk], Optional[PlanetChunk]]
        self.data = tuple([False] * 16 * 16)
        self._mesh = None  # type: Optional[trimesh.Trimesh]

    def get_planet(self):
        # type: () -> Planet
        return self.parent.get_planet()

    def get_tree_depth(self):
        return self.parent.get_tree_depth() + 1

    def get_height(self):
        tree_depth = self.get_tree_depth()
        planet = self.get_planet()
        return planet.chunk_height / astropy_healpix.level_to_nside(tree_depth)

    def get_radial_distance(self):
        # type: () -> float
        """ Get the distance from the center of the planet to the center of this node
        """
        result = self.parent.get_radial_distance()
        half_height = self.get_height() / 2
        if self.index & 0b010:
            result += half_height
        else:
            result -= half_height
        return result

    def get_healpix_index(self):
        parent_index = self.parent.get_healpix_index()
        index = 0
        # TODO: this section is probably wrong... need to check what +x and +z in octree indexes means in healpix indexes
        if self.index & 0b100:
            index |= 0b10
        if self.index & 0b001:
            index |= 0b01
        return parent_index * 4 + index

    def get_spherical_coordinates(self, dx=None, dy=None):
        # type: (Optional[float], Optional[float]) -> Tuple[float, float, float]
        """ Compute the spherical coordinates for a point within this chunk

        Args:
            dx (Optional[float]): x-offset inside the HEALPix pixel, which
                must be in the range [0:1] (0.5 is the center of the HEALPix
                pixels). If not specified, the position at the center of the
                pixel is used.
            dy (Optional[float]): y-offset inside the HEALPix pixel, which
                must be in the range [0:1] (0.5 is the center of the HEALPix
                pixels). If not specified, the position at the center of the
                pixel is used.

        Returns:
            Tuple[float, float, float]: distance from planet's core, longitude
                (radians), and latitude (radians)
        """
        healpix_index = self.get_healpix_index()
        tree_depth = self.get_tree_depth()
        nside = astropy_healpix.level_to_nside(tree_depth)
        longitude, latitude = astropy_healpix.healpix_to_lonlat(
            healpix_index,
            nside,
            dx=dx,
            dy=dy,
            order='nested',
        )
        radial_distance = self.get_radial_distance()
        return radial_distance, longitude.value, latitude.value

    def compute_vertexes(self):
        # TODO: implement properly
        healpix_index = self.get_healpix_index()
        tree_depth = self.get_tree_depth()
        nside = astropy_healpix.level_to_nside(tree_depth)
        vertexes = []
        for x in range(16):
            dx = x / 16.0
            for y in range(16):
                dy = y / 16.0
                radial_distance, lon, lat = self.get_spherical_coordinates(dx, dy)
                lon, lat = astropy_healpix.healpix_to_lonlat(healpix_index, nside, dx=dx, dy=dy, order='nested')
                vertex = utils.lonlat_to_cartesian(lon.value, lat.value)
                vertex *= radial_distance
                vertexes.append(vertex)

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
