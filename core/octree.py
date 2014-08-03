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
class AbstractOctreeBase(abstract_tree.AbstractTreeBase):
    @property
    def _leaf_cls(self):
        return OctreeLeaf

    @property
    def _interior_cls(self):
        return OctreeInterior

class OctreeInterior(abstract_tree.AbstractTreeInterior, AbstractOctreeBase):
    pass

class OctreeLeaf(abstract_tree.AbstractTreeLeaf, AbstractOctreeBase):
    pass

class Octree(abstract_tree.AbstractTree, OctreeInterior):
    pass

