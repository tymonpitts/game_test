from . import Point

__all__ = ['AbstractTree', 'TreeNode']

class TreeNode(object):
    """ A temporary proxy to store runtime information about a node.

    Instances of this class should not be stored.

    The only permanent data for a node is the actual data of the node itself.
    For example, leaf nodes in a World tree will only store their block id and
    branch nodes store a list of child data.
    """
    def __init__(self, data, tree, parent, index):
        """
        :param Any data: The data for this node.  This could be anything but
            it's worth noting that a branch node is denoted by having its data
            be a list of child data.
        :param AbstractTree tree: The tree this node belongs to.
        :type parent: TreeNode | None
        :param int index: This node's index in its parent's list of children
        """
        self.index = index
        self.parent = parent
        self.tree = tree
        self._data = data

        # Setup storage for cached values
        self._size = None
        self._origin = None
        self._children = None
        self._depth = None

    def _set_data(self, value):
        """ Set the data for this node ensuring that the parent node's child
        list is updated appropriately

        :param Any value: The new data value
        """
        self._data = value
        try:
            self.parent._data[self.index] = self._data
        except AttributeError:  # parent is None
            assert self.parent is None
            pass

    def is_leaf(self):
        """ Return whether or not this node is a leaf node (i.e. has no children)

        :rtype: bool
        """
        return not self.is_branch()

    def is_branch(self):
        """ Return whether or not this node is a branch node (i.e. has children).

        Note that this check will not be accurate if the leaf node data type is a list.

        :rtype: bool
        """
        return isinstance(self._data, list)

    def _cached__get_children(self):
        """ Get a list of child nodes for this node

        :rtype: tuple[TreeNode]
        """
        return self._children

    def get_children(self):
        """ Get a list of child nodes for this node

        The result of this function will be cached so subsequent calls will be faster.

        :rtype: tuple[TreeNode]
        """
        if self.is_leaf():
            self._children = tuple()
            self.get_children = self._cached__get_children
            return self._children
        # some subclasses may add extra data to branch nodes so be sure to only get data from the actual child nodes
        children_data = self._data[:self.tree.child_array_size]
        create_node_proxy = self.tree._create_node_proxy
        self._children = (
            create_node_proxy(child_data, parent=self, index=child_index)
            for child_index, child_data in enumerate(children_data)
        )
        self.get_children = self._cached__get_children
        return self._children

    def get_closest_child(self, point):
        """ Return the child node closest to the provided point

        :type point: Point

        :rtype: TreeNode
        """
        index = 0
        origin = self.get_origin()
        for i, num in enumerate(self.tree.BITWISE_NUMS):
            if point[i] >= origin[i]:
                index |= num
        child_node = self._data[index]
        return self.tree._create_node_proxy(child_node, parent=self, index=index)

    def _cached__get_depth(self):
        """ Get the depth of this node in the tree

        :rtype: int
        """
        return self._depth

    def get_depth(self):
        """ Get the depth of this node in the tree

        :rtype: int
        """
        try:
            return self.parent.get_depth() + 1
        except AttributeError:  # no parent so this must be the root node
            assert self.parent is None
            return 0

    def _cached__get_size(self):
        """ Return the cached size of this node.

        :rtype: float
        """
        return self._size

    def get_size(self):
        """ Get the size of this node.

        The result of this function will be cached so subsequent calls will be faster.

        :rtype: float
        """
        try:
            parent_size = self.parent.get_size()
        except AttributeError:  # no parent so this must be the root node
            assert self.parent is None
            parent_size = self.tree.size
        self._size = parent_size / 2.0
        self.get_size = self._cached__get_size
        return self._size

    def _cached__get_origin(self):
        """ Get the cached center point of this node

        :rtype: Point
        """
        return self._origin

    def get_origin(self):
        """ Get the center point of this node

        The result of this function will be cached so subsequent calls will be faster.

        :rtype: Point
        """
        try:
            origin = Point( *self.parent.get_origin() )
        except AttributeError:  # no parent so this must be the root node
            assert self.parent is None
            origin = Point()
        half_size = self.get_size() / 2.0
        index = self.index
        for i, num in enumerate(self.tree.BITWISE_NUMS):
            if index & num:
                origin[i] += half_size
            else:
                origin[i] -= half_size
        self._origin = origin
        self.get_origin = self._cached__get_origin
        return self._origin

class AbstractTree(object):
    DIMENSIONS = None  # Abstract
    """:type: int"""

    BITWISE_NUMS = None  # Abstract
    """:type: tuple[int]"""

    def __init__(self, size, max_depth):
        self.child_array_size = 2 ** self.DIMENSIONS
        self.size = float(size)  # type: float
        self.max_depth = int(max_depth)  # type: int
        self.min_size = self.size / 2.0 ** self.max_depth  # type: float
        self._root = self._create_root()

    def _create_root(self):
        """
        :rtype: list
        """
        return [None] * self.child_array_size

    def get_origin(self):
        """
        :rtype: Point
        """
        return Point()

    def _create_node_proxy(self, data, parent=None, index=0):
        """
        :rtype: TreeNode
        """
        return TreeNode(data, tree=self, parent=parent, index=index)

    def get_node(self, point, max_depth=None):
        """ Get the leaf node that contains the provided point

        :param Point point: get the leaf node that contains this point
        :param int max_depth: The maximum depth to traverse.  If this depth is
            reached before finding a leaf node then the branch node is returned.

        :rtype: TreeNode
        """
        half_size = self.size / 2.0
        for i in xrange(self.DIMENSIONS):
            if abs(point[i]) > half_size:
                return None

        node = self._create_node_proxy(self._root)
        depth = 0
        while not node.is_leaf() and (max_depth is None or depth <= max_depth):
            node = node.get_closest_child(point)
            depth += 1

        return node

