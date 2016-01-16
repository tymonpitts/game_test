from . import Point

__all__ = ['AbstractTree', 'AbstractTreeBranch', 'AbstractTreeLeaf']

class AbstractTreeBranch(object):
    _TREE_CLS = None

    def __init__(self):
        self._children = [None] * (2**self._TREE_CLS._DIMENSIONS)

    def _get_child_info(self, info, index, copy=True):
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
            yield (child, self._get_child_info(info, index))

    def _get_point(self, info, point):
        index = self._child_index_closest_to_point(info, point)
        child_info = self._get_child_info(info, index)
        try:
            return self._children[index]._get_point(child_info, point)
        except AttributeError:  # child is None
            assert self._children[index] is None
            return self._generate_point(info, point)

    def _generate_point(self, info, point):
        raise NotImplementedError

    def _child_index_closest_to_point(self, info, point):
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

    def _get_point(self, info, point):
        return self, info


class AbstractTree(object):
    _LEAF_CLS = None
    _BRANCH_CLS = None
    _DIMENSIONS = None
    _BITWISE_NUMS = None

    def __init__(self, size):
        self._size = size
        self._root = None
        self._root = self._create_root()

    def _create_root(self):
        return self._BRANCH_CLS()

    def _get_info(self):
        info = dict()
        info['level'] = 1
        info['size'] = self.size()
        info['origin'] = self.origin()
        info['parents'] = [self]
        return info

    def origin(self):
        return Point()

    def size(self):
        return self._size

    def get_point(self, point):
        half_size = self.size() / 2.0
        for i in xrange(self._DIMENSIONS):
            if abs(point[i]) > half_size:
                return (None, None)
        return self._root._get_point(self._get_info(), point)


AbstractTreeBranch._TREE_CLS = AbstractTree
AbstractTreeLeaf._TREE_CLS = AbstractTree

AbstractTree._LEAF_CLS = AbstractTreeLeaf
AbstractTree._BRANCH_CLS = AbstractTreeBranch

