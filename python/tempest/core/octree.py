__all__ = ['Octree']

#============================================================================#
#================================================================= IMPORTS ==#
from . import abstract_tree


#============================================================================#
#=================================================================== CLASS ==#
class _OctreeBranch(abstract_tree.AbstractTreeBranch):
    pass


class _OctreeLeaf(abstract_tree.AbstractTreeLeaf):
    pass


class Octree(abstract_tree.AbstractTree):
    """
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
    _DIMENSIONS = 3
    _BITWISE_NUMS = (1, 2, 4)


_OctreeBranch._TREE_CLS = Octree
_OctreeLeaf._TREE_CLS = Octree

Octree._LEAF_CLS = _OctreeLeaf
Octree._BRANCH_CLS = _OctreeBranch

