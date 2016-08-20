from typing import List, Tuple, Union

from . import decorators
from . import Point

__all__ = ['AbstractTree', 'TreeNode']

class TreeNode(object):
    """ A temporary proxy to store runtime information about a node.

    Instances of this class should not be stored.

    The only permanent data for a node is the actual data of the node itself.
    For example, leaf nodes in a World tree will only store their block id and
    branch nodes store a list of child data.
    """
    __metaclass__ = decorators.EnableCachedMethods

    def __init__(self, data, tree, parent, index):
        """

        Args:
            data (Any): The data for this node.  This could be anything but
                it's worth noting that a branch node is denoted by having its
                data be a list of child data.
            tree (AbstractTree): The tree this node belongs to.
            parent (Union[TreeNode, None]):
            index (int): This node's index in its parent's list of children
        """
        self.index = index
        self.parent = parent
        self.tree = tree
        self._data = data

    def _set_data(self, value):
        """ Set the data for this node ensuring that the parent node's child
        list is updated appropriately

        Args:
            value (Any): The new data value
        """
        self._data = value
        try:
            self.parent._data[self.index] = self._data
        except AttributeError:  # parent is None
            assert self.parent is None
            pass

    def is_leaf(self):
        """ Return whether or not this node is a leaf node (i.e. has no children)

        Returns:
            bool
        """
        return not self.is_branch()

    def is_branch(self):
        """ Return whether or not this node is a branch node (i.e. has children).

        Note that this check will not be accurate if the leaf node data type is a list.

        Returns:
            bool
        """
        return isinstance(self._data, list)

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
        children_data = self._data[:self.tree.child_array_size]
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
        for i, num in enumerate(self.tree.BITWISE_NUMS):
            if point[i] >= origin[i]:
                index |= num
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
        for i, num in enumerate(self.tree.BITWISE_NUMS):
            if index & num:
                result[i] += half_size
            else:
                result[i] -= half_size
        return result

class AbstractTree(object):
    """ Base class for all spacial tree structures (e.g. QuadTree, Octree, etc...)

    Attributes:
        child_array_size (int): The number of children the tree can have.
            This attribute is read only.
        size (int): The spacial size of the tree
            This attribute is read only.
        max_depth (int): The maximum allowed depth of the tree
            This attribute is read only.
        min_size (float): The minimum allowed size of a node within the tree.
            This attribute is read only.
    """
    # Abstract: must be reimplemented in base classes
    # This defines how many dimensions the tree has
    DIMENSIONS = None  # type: int

    # Abstract: must be reimplemented in base classes
    # This defines how child indexes are determined and should contain an
    # entry for every dimension.
    BITWISE_NUMS = None  # type: Tuple[int]

    def __init__(self, size, max_depth):
        self.child_array_size = 2 ** self.DIMENSIONS
        self.size = float(size)
        self.max_depth = int(max_depth)
        self.min_size = self.size / 2.0 ** self.max_depth
        self._root = self._create_root()

    def _create_root(self):
        """
        Returns:
            List[None]
        """
        return [None] * self.child_array_size

    def _create_node_proxy(self, data, parent=None, index=0):
        """
        Returns:
            TreeNode
        """
        return TreeNode(data, tree=self, parent=parent, index=index)

    def get_node(self, point, max_depth=None):
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

        node = self._create_node_proxy(self._root)
        depth = 0
        max_depth = max_depth if max_depth is not None else self.max_depth
        while depth < max_depth:
            if node_matches():
                return node
            node = node.get_closest_child(point)
            depth += 1

        return node

