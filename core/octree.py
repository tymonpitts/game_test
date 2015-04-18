__all__ = ['Octree']

#============================================================================#
#================================================================= IMPORTS ==#
import os
import sys
import math
import numpy
import random

from OpenGL import GL

from . import Point
from . import Vector
from . import Matrix
from . import BoundingBox

from .logger import log, increase_tab, decrease_tab, Logger

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

