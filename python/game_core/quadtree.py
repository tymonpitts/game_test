from . import abstract_tree

__all__ = ['QuadTree']

class QuadTree(abstract_tree.AbstractTree):
    """ 2 dimensional tree storage

    Child indices:
        +y  2 3
        -y  0 1
           -x +x
    """
    DIMENSIONS = 2

