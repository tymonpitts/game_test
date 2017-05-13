
"""Times access to an octree

Best Results:

Initializing...
Access Point: [1000000.0, -120245.0, 930412.0]
Initialized: time=0.00049090385437
Time for 1000 accesses: 0.294078111649

"""
import time
from game_core.octree import Octree, _OctreeBranch
from game_core import Point

# fill tree to 16 levels
#
print 'Initializing...'
start_time = time.time()
levels = 23  # worst case: 23 levels, world size=8388608m, 4 patches around with patch size=2097152m, smallest blocks=1/4m
tree = Octree(2**(levels-2))
access_point = Point(1000000, -120245, 930412)
print 'Access Point: %s' % access_point
branch = tree._root
""":type: `_OctreeBranch`"""
num_children = 2**tree._DIMENSIONS
info = tree._get_info()
for level in xrange(levels):
    branch._children = [tree._LEAF_CLS() for i in xrange(num_children)]
    if level != (levels-1):
        index = branch._child_index_closest_to_point(info, access_point)
        branch._children[index] = tree._BRANCH_CLS()
        branch.get_child_info(info, index, copy=False)
        branch = branch._children[index]
print 'Initialized: time=%s' % (time.time() - start_time)

# time access
#
start_time = time.time()
num = 1000
for i in xrange(num):
    tree.get_node(access_point)
t = time.time() - start_time
print 'Time for %s accesses: %s' % (num, t)

# import random
# import time
# from game_core import Octree
# from game_core import Point
#
# # fill tree to 16 levels
# #
# print 'Initializing...'
# start_time = time.time()
# levels = 8
# tree = Octree(2**levels)
# print 'Tree size: %s' % tree.size()
# items = [tree._root]
# num_children = 2**tree._DIMENSIONS
# for level in xrange(levels-1):
#     level_time = time.time()
#     next_items = []
#     for item in items:
#         item._children = [tree._BRANCH_CLS() for i in xrange(num_children)]
#         next_items.extend( item._children )
#     items = next_items
#     print '  Initialized level %s branches: %s' % (level+1, time.time()-level_time)
# print 'Initialized branches: %s' % (time.time() - start_time)
# start_time = time.time()
# for item in items:
#     item._children = [tree._LEAF_CLS('data') for i in xrange(num_children)]
# print 'Initialized level %s leaves:   %s' % (levels, time.time() - start_time)
#
# # time access
# #
# start_time = time.time()
# num = 1000
# for i in xrange(num):
#     half_size = tree.size() / 2
#     x = float( random.randrange(-half_size, half_size-1) ) + 0.5
#     y = float( random.randrange(-half_size, half_size-1) ) + 0.5
#     z = float( random.randrange(-half_size, half_size-1) ) + 0.5
#     tree.get_point( Point(x,y,z) )
# print 'Access time (num=%s): %s' % (num, time.time() - start_time)
#
