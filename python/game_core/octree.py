from . import abstract_tree

__all__ = ['Octree']

class Octree(abstract_tree.AbstractTree):
    """ 3 dimensional tree storage

    Child indices:
            +y:

        -z  2 3
        +z  6 7
           -x +x

            -y:

        -z  0 1
        +z  4 5
           -x +x
    """
    DIMENSIONS = 3
    BITWISE_NUMS = (1, 2, 4)

