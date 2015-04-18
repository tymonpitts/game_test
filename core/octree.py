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
    _DIMENSIONS = 3


_OctreeBranch._TREE_CLS = Octree
_OctreeLeaf._TREE_CLS = Octree

Octree._LEAF_CLS = _OctreeLeaf
Octree._BRANCH_CLS = _OctreeBranch

