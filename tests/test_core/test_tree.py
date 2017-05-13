import game_core
import unittest

class TreeTestCase(unittest.TestCase):
    def setUp(self):
        data = [
            [0, 1, 2, 3],
            [4, 5, 6, 7],
            [8, 9, 10, 11],
            [12, 13, 14, 15],
        ]
        self.tree = game_core.QuadTree(8, 3)
        self.tree._root = data

    def test_init(self):
        assert self.tree.size == 8.0
        assert self.tree.max_depth == 3
        assert self.tree.min_size == 1.0

    def test_get_node(self):
        # check depth=0
        assert self.tree.get_node(game_core.Point())._data is self.tree._root

        # check depth=1
        assert self.tree.get_node(game_core.Point(-2.0, -2.0))._data is self.tree._root[0]
        assert self.tree.get_node(game_core.Point(2.0, -2.0))._data is self.tree._root[1]
        assert self.tree.get_node(game_core.Point(-2.0, 2.0))._data is self.tree._root[2]
        assert self.tree.get_node(game_core.Point(2.0, 2.0))._data is self.tree._root[3]

        # check depth=2
        assert self.tree.get_node(game_core.Point(-3.0, -3.0))._data is self.tree._root[0][0]
        assert self.tree.get_node(game_core.Point(-1.0, -3.0))._data is self.tree._root[0][1]
        assert self.tree.get_node(game_core.Point(-3.0, -1.0))._data is self.tree._root[0][2]
        assert self.tree.get_node(game_core.Point(-1.0, -1.0))._data is self.tree._root[0][3]

        assert self.tree.get_node(game_core.Point(1.0, -3.0))._data is self.tree._root[1][0]
        assert self.tree.get_node(game_core.Point(3.0, -3.0))._data is self.tree._root[1][1]
        assert self.tree.get_node(game_core.Point(1.0, -1.0))._data is self.tree._root[1][2]
        assert self.tree.get_node(game_core.Point(3.0, -1.0))._data is self.tree._root[1][3]

        assert self.tree.get_node(game_core.Point(-3.0, 1.0))._data is self.tree._root[2][0]
        assert self.tree.get_node(game_core.Point(-1.0, 1.0))._data is self.tree._root[2][1]
        assert self.tree.get_node(game_core.Point(-3.0, 3.0))._data is self.tree._root[2][2]
        assert self.tree.get_node(game_core.Point(-1.0, 3.0))._data is self.tree._root[2][3]

        assert self.tree.get_node(game_core.Point(1.0, 1.0))._data is self.tree._root[3][0]
        assert self.tree.get_node(game_core.Point(3.0, 1.0))._data is self.tree._root[3][1]
        assert self.tree.get_node(game_core.Point(1.0, 3.0))._data is self.tree._root[3][2]
        assert self.tree.get_node(game_core.Point(3.0, 3.0))._data is self.tree._root[3][3]
