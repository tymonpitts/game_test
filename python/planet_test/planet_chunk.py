from __future__ import absolute_import, division, print_function

import astropy_healpix
from typing import Optional, Tuple, TYPE_CHECKING

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
        self.vertexes = None

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

    def get_spherical_coordinates(self):
        # type: () -> Tuple[float, float, float]
        healpix_index = self.get_healpix_index()
        tree_depth = self.get_tree_depth()
        nside = astropy_healpix.level_to_nside(tree_depth)
        longitude, latitude = astropy_healpix.healpix_to_lonlat(healpix_index, nside, order='nested')
        radial_distance = self.get_radial_distance()
        return radial_distance, longitude.value, latitude.value

    def compute_vertexes(self):
        # TODO: implement properly
        radial_distance, longitude, latitude = self.get_spherical_coordinates()
        # for now just initialize 1 vert for the center of this chunk
        self.vertex = utils.lonlat_to_cartesian(longitude, latitude)
        self.vertex *= radial_distance
