from typing import TYPE_CHECKING
from .planet_chunk import PlanetChunk

if TYPE_CHECKING:
    # guarded imports to prevent circular dependencies
    from .planet import Planet


class PlanetTopChunk(PlanetChunk):
    """ Represents a `PlanetChunk` that is a direct child of the `Planet` itself

    Subclassing because `PlanetChunk` assumes its `parent` is another PlanetChunk
    but this subclass will assume it is a `Planet`
    """
    def __init__(self, parent, index):
        # type: (Planet, int) -> None
        # noinspection PyTypeChecker
        super(PlanetTopChunk, self).__init__(parent=None, index=index)
        self.parent = parent  # type: Planet

    def get_radial_distance(self):
        return self.get_planet().radius

    def get_planet(self):
        # type: () -> Planet
        return self.parent

    def get_tree_depth(self):
        return 0

    def get_healpix_index(self):
        return self.index
