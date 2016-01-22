from . import Point

__all__ = ['AbstractTree', 'AbstractTreeBranch', 'AbstractTreeLeaf']

class AbstractTreeBranch(object):
    _TREE_CLS = None

    def __init__(self):
        self._children = [None for i in xrange(2**self._TREE_CLS._DIMENSIONS)]
        """:type: list[None|`AbstractTreeBranch`|`AbstractLeafBranch`]"""

    def get_child_info(self, info, index, copy=True):
        if copy:
            info = info.copy()
            info['origin'] = info['origin'].copy()
            info['parents'] = list(info['parents'])
        info['level'] += 1
        info['size'] *= 0.5
        info['index'] = index
        info['parents'].append(self)

        half_size = info['size'] * 0.5
        offset = []
        for i, num in enumerate(self._TREE_CLS._BITWISE_NUMS):
            offset.append( half_size if index&num else -half_size )

        for i, component in enumerate(offset):
            info['origin'][i] += component

        return info

    def iter_children_info(self, info):
        for index, child in enumerate(self._children):
            yield (child, self.get_child_info(info, index, copy=True))

    def get_max_depth_node(self, info, point, max_depth):
        if info['level'] >= max_depth:
            return self, info
        index = self.get_closest_child_index(info, point)
        child_info = self.get_child_info(info, index, copy=True)
        try:
            return self._children[index].get_max_depth_node(child_info, point, max_depth)
        except AttributeError:  # child is None
            assert self._children[index] is None
            return self.generate_node(info, point, max_depth, child_info)

    def get_node(self, info, point):
        index = self.get_closest_child_index(info, point)
        child_info = self.get_child_info(info, index, copy=True)
        try:
            return self._children[index].get_node(child_info, point)
        except AttributeError:  # child is None
            if self._children[index] is not None:
                raise
            return self.generate_node(info, point, child_info=child_info)

    def generate_node(self, info, point, max_depth=None, child_info=None):
        raise NotImplementedError

    def get_closest_child_index(self, info, point):
        index = 0
        origin = info['origin']
        for i,num in enumerate(self._TREE_CLS._BITWISE_NUMS):
            if point[i] >= origin[i]: index |= num

        return index

class AbstractTreeLeaf(object):
    _TREE_CLS = None

    def __init__(self, data=None):
        self._data = data

    def data(self):
        return self._data

    def set_data(self, data):
        self._data = data
        # TODO: possibly merge here

    def get_node(self, info, point):
        return self, info

    def get_max_depth_node(self, info, point, max_depth):
        return self, info

class AbstractTree(object):
    _LEAF_CLS = None
    _BRANCH_CLS = None
    _DIMENSIONS = None
    _BITWISE_NUMS = None

    def __init__(self, size, max_depth):
        self._size = size
        self._max_depth = max_depth
        self._root = self._create_root()

    def _create_root(self):
        return self._BRANCH_CLS()

    def _get_info(self):
        info = dict()
        info['level'] = 1
        info['max_depth'] = self.max_depth()
        info['size'] = self.size()
        info['origin'] = self.origin()
        info['parents'] = []
        info['tree'] = self
        return info

    def origin(self):
        return Point()

    def size(self):
        return self._size

    def max_depth(self):
        return self._max_depth

    def get_node(self, point, max_depth=None):
        half_size = self.size() / 2.0
        for i in xrange(self._DIMENSIONS):
            if abs(point[i]) > half_size:
                return (None, None)
        if max_depth is None:
            return self._root.get_node(self._get_info(), point)
        else:
            return self._root.get_max_depth_node(self._get_info(), point, max_depth)

AbstractTreeBranch._TREE_CLS = AbstractTree
AbstractTreeLeaf._TREE_CLS = AbstractTree

AbstractTree._LEAF_CLS = AbstractTreeLeaf
AbstractTree._BRANCH_CLS = AbstractTreeBranch

