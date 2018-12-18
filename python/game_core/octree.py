__all__ = ['Octree']

from . import abstract_tree


class Octree(abstract_tree.AbstractTree):
    """ 3 dimensional tree storage

    Child indices:

           2      3
                        ^
      6      7          y
                       z x >
           0      1   L

      4      5

    """
    DIMENSIONS = 3
