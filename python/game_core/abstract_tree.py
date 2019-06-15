__all__ = ['AbstractTree', 'TreeNode']

from typing import Any, List, Optional, Tuple

from . import decorators
from . import BoundingBox
from . import Point
from . import Vector


class TreeNode(object):
    """ A temporary proxy to store runtime information about a node.

    Instances of this class should not be stored.

    The only permanent data for a node is the actual data of the node itself.
    For example, leaf nodes in a World tree will only store their block id and
    branch nodes store a list of child data.
    """
    __metaclass__ = decorators.EnableCachedMethods

    def __init__(self, data, tree, parent, index):
        # type: (_TreeNodeData, AbstractTree, Optional[TreeNode], int) -> None
        """
        Args:
            data (_TreeNodeData): All data for this node including this node's
                value and list of children
            tree (AbstractTree): The tree this node belongs to.
            parent (Optional[TreeNode]):
            index (int): This node's index in its parent's list of children
        """
        self.index = index
        self.parent = parent  # type: Optional[TreeNode]
        self.tree = tree
        self._data = data

    @decorators.cached_method
    def index_hierarchy(self):
        # type: () -> Tuple[int, ...]
        if not self.parent:
            return (self.index, )
        return tuple(list(self.parent.index_hierarchy()) + [self.index])

    def __str__(self):
        if self.is_leaf():
            return '%s(type="leaf", depth=%s, index=%s, origin=%s, data=%s)' % (self.__class__.__name__, self.get_depth(), self.index, self.get_origin(), self._data)
        else:
            return '%s(type="branch", depth=%s, index=%s, origin=%s)' % (self.__class__.__name__, self.get_depth(), self.index, self.get_origin())

    def get_value(self):
        return self._data.value

    def set_value(self, value):
        self._data.value = value

    def split(self):
        # TODO: clear get_children cache
        # TODO: validate we haven't already split?
        self._data.children = [_TreeNodeData(value=self.tree._get_default_node_data()) for i in range(self.tree.num_children)]

    def is_leaf(self):
        """ Return whether or not this node is a leaf node (i.e. has no children)

        Returns:
            bool
        """
        return self._data.children is None

    def is_branch(self):
        """ Return whether or not this node is a branch node (i.e. has children).

        Returns:
            bool
        """
        return self._data.children is not None

    @decorators.cached_method
    def get_children(self):
        """ Get a list of child nodes for this node

        The result of this function will be cached so subsequent calls will be faster.

        Returns:
            Tuple[TreeNode]
        """
        if self.is_leaf():
            return tuple()

        # some subclasses may add extra data to branch nodes so be sure to only get data from the actual child nodes
        children_data = self._data.children
        create_node_proxy = self.tree._create_node_proxy
        return tuple(
            create_node_proxy(child_data, parent=self, index=child_index)
            for child_index, child_data in enumerate(children_data)
        )

    def get_closest_child(self, point):
        """ Return the child node closest to the provided point

        .. warning:: This does NOT do any error checking for leaf nodes.
            It is up to the caller do perform these checks.

        Args:
            point (Point)

        Returns:
            TreeNode
        """
        index = 0
        origin = self.get_origin()
        for i, dimension_bit in enumerate(self.tree.dimension_bits):
            if point[i] >= origin[i]:
                index |= dimension_bit
        return self.get_children()[index]

    @decorators.cached_method
    def get_depth(self):
        """ Get the depth of this node in the tree

        The result of this function will be cached so subsequent calls will be faster.

        Returns:
            int
        """
        try:
            return self.parent.get_depth() + 1
        except AttributeError:  # no parent so this must be the root node
            assert self.parent is None
            return 0

    @decorators.cached_method
    def get_size(self):
        """ Get the size of this node.

        The result of this function will be cached so subsequent calls will be faster.

        Returns:
            float
        """
        try:
            parent_size = self.parent.get_size()
        except AttributeError:  # no parent so this must be the root node
            assert self.parent is None
            return self.tree.size
        return parent_size / 2.0

    @decorators.cached_method
    def get_origin(self):
        """ Get the center point of this node

        The result of this function will be cached so subsequent calls will be faster.

        Returns:
            Point
        """
        try:
            result = Point( *self.parent.get_origin() )
        except AttributeError:  # no parent so this must be the root node
            assert self.parent is None
            return Point()
        half_size = self.get_size() / 2.0
        index = self.index
        for i, dimension_bit in enumerate(self.tree.dimension_bits):
            if index & dimension_bit:
                result[i] += half_size
            else:
                result[i] -= half_size
        return result

    @decorators.cached_method
    def get_bounds(self):
        # type: () -> BoundingBox
        """ Get the bounding box of this node based on its origin and size

        The result of this function will be cached so subsequent calls will be faster.

        Returns:
            BoundingBox
        """
        origin = self.get_origin()
        half_size = self.get_size() / 2.0
        half_size_vector = Vector(half_size, half_size, half_size)
        return BoundingBox(origin - half_size_vector, origin + half_size_vector)

    def get_neighbor(self, dimension, negative):
        if not self.parent:
            return None
        neighbor_index = self.tree.neighbor_sibling_indexes[self.index][dimension]
        if self.index & self.tree.dimension_bits[dimension]:
            if negative:
                return self.parent.get_children()[neighbor_index]
            else:
                # TODO: this doesn't account for sparse trees
                parent_neighbor = self.parent.get_neighbor(dimension, negative)
                if parent_neighbor is None:
                    return None
                if parent_neighbor.is_leaf():
                    return parent_neighbor
                return parent_neighbor.get_children()[neighbor_index]
        elif not negative:
            return self.parent.get_children()[neighbor_index]
        else:
            parent_neighbor = self.parent.get_neighbor(dimension, negative)
            if parent_neighbor is None:
                return None
            if parent_neighbor.is_leaf():
                return parent_neighbor
            return parent_neighbor.get_children()[neighbor_index]

    @decorators.cached_method
    def get_neighbors(self):
        # type: () -> Optional[Tuple[TreeNode, ...]]
        if not self.parent:
            return None
        result = []
        for dimension in range(self.tree.DIMENSIONS):
            result.append(self.get_neighbor(dimension, negative=True))
            result.append(self.get_neighbor(dimension, negative=False))
        return tuple(result)

    @decorators.cached_method
    def get_diagonal_neighbors(self):
        # type: () -> Optional[Tuple[TreeNode, ...]]
        neighbors = self.get_neighbors()
        if not neighbors:
            return None

        # TODO: this is not agnostic of number of dimensions
        result = list(neighbors)
        for i, neighbor in enumerate(neighbors):
            neighbor_dimension = int(i / 2)
            diagonal_dimension = neighbor_dimension - 1 if neighbor_dimension else self.tree.DIMENSIONS - 1
            result.append(neighbor.get_neighbor(diagonal_dimension, negative=True))
            result.append(neighbor.get_neighbor(diagonal_dimension, negative=False))

            if neighbor_dimension < self.tree.DIMENSIONS - 1:
                corner_dimension = diagonal_dimension - 1 if diagonal_dimension else self.tree.DIMENSIONS - 1
                result[-2].get_neighbor(corner_dimension, negative=True)
                result[-1].get_neighbor(corner_dimension, negative=False)
        assert len(result) == 26
        return tuple(result)


class _TreeNodeData(object):
    """ Internal object to store just the data of a node in a tree
    """
    def __init__(self, value=None, children=None):
        # type: (Optional[Any], Optional[List[Optional[_TreeNodeData]]]) -> None
        self.value = value
        self.children = children


class AbstractTree(object):
    """ Base class for all spacial tree structures (e.g. QuadTree, Octree, etc...)

    All attributes are considered read-only

    Attributes:
        dimension_bits (Tuple[int, ...]): A tuple of single bits whose length
            matches the tree's dimensions. This is used to define how
            child indexes are determined.
        num_children (int): The number of children the tree can have.
        neighbor_sibling_indexes (Tuple[Tuple[int, ...]]): Indexes for each child's adjacent siblings
        size (int): The spacial size of the tree
        max_depth (int): The maximum allowed depth of the tree
        min_size (float): The minimum allowed size of a node within the tree.
    """
    # Abstract: must be reimplemented in base classes
    # This defines how many dimensions the tree has
    DIMENSIONS = None  # type: int

    def __init__(self, size, max_depth):
        # TODO: remove size from base class. it is not always relevant
        self.dimension_bits = tuple(1 << i for i in range(self.DIMENSIONS))
        self.num_children = 2 ** self.DIMENSIONS
        self.neighbor_sibling_indexes = tuple(
            tuple(i ^ b for b in self.dimension_bits)
            for i in range(self.num_children)
        )

        self.size = float(size)
        self.max_depth = int(max_depth)
        self.min_size = self.size / 2.0 ** self.max_depth
        self._data = _TreeNodeData(value=self._get_default_node_data())

    def _get_default_node_data(self):
        return None

    def _create_node_proxy(self, data, parent=None, index=0):
        # type: (_TreeNodeData, Optional[TreeNode], int) -> TreeNode
        return TreeNode(data, tree=self, parent=parent, index=index)

    def get_opposite_index(self, index):
        """ Flip the bits for the provided index

        NOTE: we can't just use the "~" operator here because that does
              also flips the sign of the number (e.g. ~0b010 = -0b11)

        Args:
            index (int): int with the same number of bits as this tree has dimensions

        Returns:
            int: ``index`` with its dimension bits flipped
        """
        result = index
        for dimension_bit in self.dimension_bits:
            result ^= dimension_bit
        return result

    def get_root(self):
        return self._create_node_proxy(self._data)

    def get_node_from_point(self, point, max_depth=None):
        """ Get the leaf node that contains the provided point

        Args:
            point (Point): get the leaf node that contains this point
            max_depth (int): The maximum depth to traverse.  If this depth is
                reached before finding a leaf node then the branch node is
                returned.

        Returns:
            TreeNode
        """
        def node_matches():
            if node.get_origin() == point:
                return True
            elif node.is_leaf():
                return True
            else:
                return False

        half_size = self.size / 2.0
        for i in xrange(self.DIMENSIONS):
            if abs(point[i]) > half_size:
                return None

        node = self._create_node_proxy(self._data, parent=None, index=0)
        depth = 0
        max_depth = max_depth if max_depth is not None else self.max_depth
        while depth < max_depth:
            if node_matches():
                return node
            node = node.get_closest_child(point)
            depth += 1

        return node

