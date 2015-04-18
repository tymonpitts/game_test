import time
from collections import OrderedDict
from ... import core

_BLOCKS = []


class BlockMeta(type):
    def __new__(meta, name, bases, dct):
        cls = super(BlockMeta, meta).__new__(meta, name, bases, dct)
        if not name.startswith('Abstract'):
            global _BLOCKS
            _BLOCKS.append(cls)
        return cls


class AbstractBlock(object):
    __metaclass__ = BlockMeta
    _ID_TO_STATE = {}
    def __init__(self, game, octree_item, octree_item_info):
        super(AbstractBlock, self).__setattr__('_attributes', self.attributes())
        self.__dict__.update(self._ID_TO_STATE[octree_item.data()])
        self._game = game
        self._origin = octree_item_info['origin'].copy()
        self._size = octree_item_info['size']
        self._world = octree_item_info['parents'][0]

    def __setattr__(self, name, value):
        if name in self._attributes:
            if value not in self._attributes[name]:
                raise ValueError('%s is not a valid value for "%s".  Valid values are: %s' % (value, name, values))
        super(AbstractBlock, self).__setattr__(name, value)

    @classmethod
    def _register_state(cls, id, state, items):
        if not items:
            cls._ID_TO_STATE[id] = state
            return (id+1)

        current = items.pop(0)
        name = current[0]
        values = current[1]
        for value in values:
            state[name] = value
            id = cls._register_state(id, state, items)
        return id

    @classmethod
    def register(cls, id):
        items = cls.attributes().items()
        state = {}
        return cls._register_state(id, {}, items)

    @classmethod
    def attributes(cls):
        return OrderedDict()

    @classmethod
    def is_solid(cls):
        return True

    def __eq__(self, other):
        if type(self) != type(other):
            return False
        return self._origin == other._origin

    def __ne__(self, other):
        return not (self == other)

    def origin(self):
        return self._origin.copy()

    def game(self):
        return self._game

    def size(self):
        return self._size

    def world(self):
        return self._world

    def bbox(self):
        half_size = self.size() * 0.5
        offset = core.Vector(half_size, half_size, half_size)
        min_ = self._origin - offset
        max_ = self._origin + offset
        return core.BoundingBox(min_, max_)

    def solve_collision(self, start_bbox, acceleration=None):
        # calculate a bounding box that encompasses the start/end bounding boxes
        #
        if acceleration:
            end_bbox = start_bbox.translate(acceleration)
            bbox = core.BoundingBox()
            bbox.bbox_expand(start_bbox)
            bbox.bbox_expand(end_bbox)
        else:
            end_bbox = start_bbox.copy()
            bbox = start_bbox.copy()

        # intersect this block's bounding box with the full movement bounding box
        #
        collision_box = self.bbox().intersection(bbox)
        if not collision_box:
            return 1.0, None

        # get a before and after position
        #
        before = start_bbox.center()
        after = end_bbox.center()
        center = collision_box.center()

        # expand the collision box to encompass potential solution positions.
        # this is so that we can find the proper solution.
        #
        expanded_collision_bbox = collision_box.copy()
        dimensions = [start_bbox.get_dimension(i) / 2.0 for i in xrange(3)]
        expanded_collision_bbox._min -= dimensions
        expanded_collision_bbox._max += dimensions

        # loop through each bounding box component and determine the shortest
        # distance along *acceleration* that will bring *bbox* out of 
        # collision.
        #
        t = 1.0
        component_index = None
        other_indices = [(1,2), (0,2), (0,1)]
        for i, others in enumerate(other_indices):
            # skip this component if the acceleration for it is 0
            #
            if acceleration[i] == 0:
                continue

            # find the bbox center position for this component that will
            # place it on the edge of this blocks bbox.  If this component 
            # is not colliding, then skip it.
            #
            if before[i] < collision_box._min[i]:
                component = collision_box._min[i]
                component -= start_bbox.get_dimension(i) / 2.0
            elif before[i] > collision_box._max[i]:
                component = collision_box._max[i]
                component += start_bbox.get_dimension(i) / 2.0
            else:
                continue

            # determine the point along the acceleration vector that 
            # intersects the component value we just found
            #
            this_t = (component - before[i]) / acceleration[i]
            this_accel = acceleration * this_t
            this_pos = before + this_accel

            # determine if the new position touches the edge of this 
            # block's bounding box
            #
            invalid = False
            for other in others:
                if this_pos[other] < expanded_collision_bbox._min[other]:
                    invalid = True
                    break
                if this_pos[other] > expanded_collision_bbox._max[other]:
                    invalid = True
                    break
            if invalid:
                continue

            # use the shortest solution acceleration
            #
            if this_t < t:
                t = this_t
                component_index = i
        return t, component_index

    def should_neighbor_generate_mesh(self, neighbor):
        return False

    def should_generate_mesh(self):
        return True
        # stime = time.time()
        # bbox = self.bbox()
        # self.world()._mesh_times['should_generate_mesh: bbox'] += time.time() - stime
        # stime = time.time()
        # blocks = set()
        # blocks.update(self.world().get_blocks(
        #         bbox, exclude_types=[], inclusive=[0]))
        # blocks.update(self.world().get_blocks(
        #         bbox, exclude_types=[], inclusive=[1]))
        # blocks.update(self.world().get_blocks(
        #         bbox, exclude_types=[], inclusive=[2]))
        # self.world()._mesh_times['should_generate_mesh: get_neighbors'] += time.time() - stime
        # stime = time.time()
        # for block in blocks:
        #     if block == self:
        #         continue
        #     if block.should_neighbor_generate_mesh(self):
        #         return True
        # self.world()._mesh_times['should_generate_mesh: neighbor_check'] += time.time() - stime
        # return False


class Air(AbstractBlock):
    @classmethod
    def is_solid(cls):
        return False

    def should_generate_mesh(self):
        return False

    def should_neighbor_generate_mesh(self, neighbor):
        return True


class Rock(AbstractBlock):
    TopConnected    = int('000001', 2)
    BottomConnected = int('000010', 2)
    RightConnected  = int('000100', 2)
    LeftConnected   = int('001000', 2)
    FrontConnected  = int('010000', 2)
    BackConnected   = int('100000', 2)
    @classmethod
    def attributes(cls):
        result = super(Rock, cls).attributes()
        result['connected'] = reversed(range(int('111111', 2)))
        return result

