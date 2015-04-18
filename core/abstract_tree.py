__all__ = ['AbstractTree']

#============================================================================#
#================================================================= IMPORTS ==#

from . import Point


#============================================================================#
#=================================================================== CLASS ==#
class AbstractTreeInterior(object):
    _TREE_CLS = None

    def __init__(self):
        num_children = pow(2, self._TREE_CLS._DIMENSIONS)
        self._children = tuple([self._TREE_CLS._LEAF_CLS() for i in xrange(num_children)])

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
        offset = [0.0, 0.0, 0.0]
        offset[0] = half_size if index&4 else -half_size
        offset[1] = half_size if index&2 else -half_size
        offset[2] = half_size if index&1 else -half_size

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
        if point.x >= origin.x: index |= 4
        if point.y >= origin.y: index |= 2
        if point.z >= origin.z: index |= 1

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
    """

    Child indices:
        top:
            2 6
            3 7
        bottom:
            0 4
            1 5
    """
    _LEAF_CLS = None
    _INTERIOR_CLS = None
    _DIMENSIONS = None

    def __init__(self, size):
        super(AbstractTree, self).__init__()
        self._root = self._INTERIOR_CLS()
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
        for i in xrange(3):
            if abs(point[i]) > half_size:
                return (None, None)
        return self._root._get_point(self._get_info(), point)


AbstractTreeInterior._TREE_CLS = AbstractTree
AbstractTreeLeaf._TREE_CLS = AbstractTree

AbstractTree._LEAF_CLS = AbstractTreeLeaf
AbstractTree._INTERIOR_CLS = AbstractTreeInterior

