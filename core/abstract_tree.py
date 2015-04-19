__all__ = ['AbstractTree']

#============================================================================#
#================================================================= IMPORTS ==#
from . import Point


#============================================================================#
#=================================================================== CLASS ==#
class AbstractTreeBranch(object):
    _TREE_CLS = None

    def __init__(self):
        self._children = None
        # num_children = pow(2, self._TREE_CLS._DIMENSIONS)
        # self._children = tuple([self._TREE_CLS._LEAF_CLS() for i in xrange(num_children)])

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
        return self._children[index]._get_point(self._get_child_info(info, index), point)

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
        super(AbstractTree, self).__init__()
        self._root = self._BRANCH_CLS()
        self._size = size

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

