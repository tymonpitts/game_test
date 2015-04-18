__all__ = ['Octree']

#============================================================================#
#================================================================= IMPORTS ==#

from . import abstract_tree


#============================================================================#
#=================================================================== CLASS ==#
class OctreeInterior(abstract_tree.AbstractTreeInterior):
    pass


class OctreeLeaf(abstract_tree.AbstractTreeLeaf):
    pass


class Octree(abstract_tree.AbstractTree):
    _DIMENSIONS = 3


OctreeInterior._TREE_CLS = Octree
OctreeLeaf._TREE_CLS = Octree

Octree._LEAF_CLS = OctreeLeaf
Octree._INTERIOR_CLS = OctreeInterior

