import unittest

import game_core
from game_core.abstract_tree import _TreeNodeData


class TreeTestCase(unittest.TestCase):
    def setUp(self):
        self.tree = game_core.QuadTree(8, 3)
        self.tree._data = _TreeNodeData(children=[
            _TreeNodeData(children=[_TreeNodeData(value=i) for i in range(0, 4)]),
            _TreeNodeData(children=[_TreeNodeData(value=i) for i in range(4, 8)]),
            _TreeNodeData(children=[_TreeNodeData(value=i) for i in range(8, 12)]),
            _TreeNodeData(children=[_TreeNodeData(value=i) for i in range(12, 16)]),
        ])

    def test_init(self):
        assert self.tree.size == 8.0
        assert self.tree.max_depth == 3
        assert self.tree.min_size == 1.0

    def test_get_node(self):
        # check depth=0
        assert self.tree.get_node_from_point(game_core.Point())._data is self.tree._data

        # check depth=1
        assert self.tree.get_node_from_point(game_core.Point(-2.0, -2.0))._data is self.tree._data.children[0]
        assert self.tree.get_node_from_point(game_core.Point(2.0, -2.0))._data is self.tree._data.children[1]
        assert self.tree.get_node_from_point(game_core.Point(-2.0, 2.0))._data is self.tree._data.children[2]
        assert self.tree.get_node_from_point(game_core.Point(2.0, 2.0))._data is self.tree._data.children[3]

        # check depth=2
        assert self.tree.get_node_from_point(game_core.Point(-3.0, -3.0))._data is self.tree._data.children[0].children[0]
        assert self.tree.get_node_from_point(game_core.Point(-1.0, -3.0))._data is self.tree._data.children[0].children[1]
        assert self.tree.get_node_from_point(game_core.Point(-3.0, -1.0))._data is self.tree._data.children[0].children[2]
        assert self.tree.get_node_from_point(game_core.Point(-1.0, -1.0))._data is self.tree._data.children[0].children[3]

        assert self.tree.get_node_from_point(game_core.Point(1.0, -3.0))._data is self.tree._data.children[1].children[0]
        assert self.tree.get_node_from_point(game_core.Point(3.0, -3.0))._data is self.tree._data.children[1].children[1]
        assert self.tree.get_node_from_point(game_core.Point(1.0, -1.0))._data is self.tree._data.children[1].children[2]
        assert self.tree.get_node_from_point(game_core.Point(3.0, -1.0))._data is self.tree._data.children[1].children[3]

        assert self.tree.get_node_from_point(game_core.Point(-3.0, 1.0))._data is self.tree._data.children[2].children[0]
        assert self.tree.get_node_from_point(game_core.Point(-1.0, 1.0))._data is self.tree._data.children[2].children[1]
        assert self.tree.get_node_from_point(game_core.Point(-3.0, 3.0))._data is self.tree._data.children[2].children[2]
        assert self.tree.get_node_from_point(game_core.Point(-1.0, 3.0))._data is self.tree._data.children[2].children[3]

        assert self.tree.get_node_from_point(game_core.Point(1.0, 1.0))._data is self.tree._data.children[3].children[0]
        assert self.tree.get_node_from_point(game_core.Point(3.0, 1.0))._data is self.tree._data.children[3].children[1]
        assert self.tree.get_node_from_point(game_core.Point(1.0, 3.0))._data is self.tree._data.children[3].children[2]
        assert self.tree.get_node_from_point(game_core.Point(3.0, 3.0))._data is self.tree._data.children[3].children[3]
