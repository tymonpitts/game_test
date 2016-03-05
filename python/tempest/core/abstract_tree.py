from . import Point

__all__ = ['AbstractTree', 'AbstractTreeBranch', 'AbstractTreeLeaf']

class AbstractTreeBranch(object):
    _TREE_CLS = None

    def __init__(self):
        self._children = [None for i in xrange(2**self._TREE_CLS._DIMENSIONS)]
        """:type: list[None|`AbstractTreeBranch`|`AbstractLeafBranch`]"""

    def set_to_child_info(self, info, index):
        info['parent_indices'].append( info['index'] )
        info['parents'].append(self)
        info['index'] = index

    def set_to_parent_info(self, info):
        info['index'] = info['parent_indices'].pop(-1)
        info['parents'].pop(-1)

    # def get_child_info(self, info, index, copy=True):
    #     if copy:
    #         info = info.copy()
    #         info['origin'] = info['origin'].copy()
    #         info['parents'] = list(info['parents'])
    #         info['parent_indices'] = list(info['parent_indices'])
    #     info['parent_indices'].append( info['index'] )
    #     info['level'] += 1
    #     info['size'] *= 0.5
    #     info['index'] = index
    #     info['parents'].append(self)
    #
    #     half_size = info['size'] * 0.5
    #     offset = []
    #     for i, num in enumerate(self._TREE_CLS._BITWISE_NUMS):
    #         offset.append( half_size if index&num else -half_size )
    #
    #     for i, component in enumerate(offset):
    #         info['origin'][i] += component
    #
    #     return info

    # TODO: yielding child_info is pointless here since info will be set to that in place
    def iter_children_info(self, info):
        """
        WARNING: If you exit the iterator prematurely then call `set_to_parent_info`.
            Otherwise `info` will be set to the info for one of this node's children.
        """
        self.set_to_child_info(info, 0)
        for index, child in enumerate(self._children):
            info['index'] = index
            yield (child, info)
        self.set_to_parent_info(info)

    def get_max_depth_node(self, info, point, max_depth):
        if len(info['parents']) > max_depth:
            return self, info
        index = self.get_closest_child_index(info, point)
        self.set_to_child_info(info, index)
        try:
            return self._children[index].get_max_depth_node(info, point, max_depth)
        except AttributeError:  # child is None
            if self._children[index] is not None:
                raise
            self.set_to_parent_info(info)
            return self.generate_node(info, point, max_depth)

    def get_node(self, info, point):
        index = self.get_closest_child_index(info, point)
        self.set_to_child_info(info, index)
        try:
            return self._children[index].get_node(info, point)
        except AttributeError:  # child is None
            if self._children[index] is not None:
                raise
            self.set_to_parent_info(info)
            return self.generate_node(info, point)

    def generate_node(self, info, point, max_depth=None):
        raise NotImplementedError

    def get_size(self, info):
        tree_size = info['tree']._size
        return tree_size ** ( 1.0/float( len(info['parents'])+1 ) )

    def get_child_origin(self, size, origin, child_index):
        result = origin.copy()
        half_child_size = size * 0.25
        for i, num in enumerate(self._TREE_CLS._BITWISE_NUMS):
            if index & num:
                result[i] += half_child_size
            else:
                result[i] -= half_child_size

    def get_origin(self, info):
        half_size = info['tree']._size * 0.5
        result = Point()
        for index in info['parent_indices'][1:]:
            half_size *= 0.5
            for i, num in enumerate(self._TREE_CLS._BITWISE_NUMS):
                if index & num:
                    result[i] += half_size
                else:
                    result[i] -= half_size
        return result

    def get_closest_child_index(self, info, point):
        index = 0
        # TODO: should probably cache this somehow so we don't have to rebuild it at every level
        origin = self.get_origin(info)
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
        self._size = float(size)
        self._max_depth = int(max_depth)
        self._min_size = self._size / 2.0 ** self._max_depth
        self._root = self._create_root()

    def _create_root(self):
        return self._BRANCH_CLS()

    def _get_info(self):
        info = dict()
        info['index'] = 0
        info['parents'] = []
        info['parent_indices'] = []
        info['tree'] = self
        return info

    def origin(self):
        return Point()

    def size(self):
        return self._size

    def max_depth(self):
        return self._max_depth

    def min_size(self):
        return self._min_size

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

