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
    pass

class AbstractOctreeParent(abstract_tree.AbstractTreeParent, AbstractOctreeBase):
    pass

class AbstractOctreeChild(abstract_tree.AbstractTreeChild, AbstractOctreeBase):
    pass

class Octree(abstract_tree.AbstractTree, AbstractOctreeParent):
    pass

class OctreeInterior(abstract_tree.AbstractTreeInterior, AbstractOctreeParent, AbstractOctreeChild):
    pass

class OctreeLeaf(abstract_tree.AbstractTreeLeaf, AbstractOctreeChild):
    pass

