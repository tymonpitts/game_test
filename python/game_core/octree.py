from . import abstract_tree

__all__ = ['Octree']

class Octree(abstract_tree.AbstractTree):
    """ 3 dimensional tree storage

    Child indices:
    
    #
    #        2      3
    #                     ^
    #   6      7          y
    #                    z x >
    #        0      1   L
    #
    #   4      5
    #
    """
    DIMENSIONS = 3
    BITWISE_NUMS = (1 << i for i in range(DIMENSIONS))
    NUM_CHILDREN = 2 ** DIMENSIONS
    NEIGHBORS = ((i ^ b for b in BITWISE_NUMS) for i in range(NUM_CHILDREN))
