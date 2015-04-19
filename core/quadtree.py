__all__ = ['QuadTree']

#============================================================================#
#================================================================= IMPORTS ==#
from . import abstract_tree


#============================================================================#
#=================================================================== CLASS ==#
class _QuadTreeBranch(abstract_tree.AbstractTreeBranch):
    pass


class _QuadTreeLeaf(abstract_tree.AbstractTreeLeaf):
    pass


class QuadTree(abstract_tree.AbstractTree):
    """
    Child indices:
        +y  2 3
        -y  0 1
           -x +x
    """
    _DIMENSIONS = 2
    _BITWISE_NUMS = (1, 2)


_QuadTreeBranch._TREE_CLS = QuadTree
_QuadTreeLeaf._TREE_CLS = QuadTree

QuadTree._LEAF_CLS = _QuadTreeLeaf
QuadTree._BRANCH_CLS = _QuadTreeBranch

