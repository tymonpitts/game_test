from . import Point
class BoundingBox(object):
    def __init__(self, min=None, max=None):
        self._min = None
        self._max = None

        if min:
            self.expand(min)
        if max:
            self.expand(max)

    def __nonzero__(self):
        return self.is_valid()

    def __str__(self):
        return '<%s min=%s max=%s>' % (self.__class__.__name__, self._min, self._max)

    def min(self):
        return self._min.copy()

    def max(self):
        return self._max.copy()

    def get_dimension(self, index):
        return self._max[index] - self._min[index]

    def width(self):
        return self.get_dimension(0)

    def height(self):
        return self.get_dimension(1)

    def depth(self):
        return self.get_dimension(2)

    def center(self):
        return Point([(self._min[i]+self._max[i]) / 2.0 for i in xrange(3)])

    def copy(self):
        bbox = BoundingBox()
        bbox._min = self._min.copy()
        bbox._max = self._max.copy()
        return bbox

    def is_valid(self):
        return self._min is not None

    def expand(self, point):
        point = Point(point)
        if self._min is None:
            self._min = point
            self._max = point.copy()
            return

        for i in xrange(3):
            self._min[i] = min(self._min[i], point[i])
            self._max[i] = max(self._max[i], point[i])

    def bbox_expand(self, other):
        if self._min is None:
            self._min = other._min.copy()
            self._max = other._max.copy()
            return

        for i in xrange(3):
            self._min[i] = min(self._min[i], other._min[i])
            self._max[i] = max(self._max[i], other._max[i])

    def volume(self):
        volume = 1.0
        for i in xrange(3):
            length = self._max[i] - self._min[i]
            volume *= length
        return volume

    def intersection(self, other, inclusive=[]):
        if not self.collides(other, inclusive):
            return None
        min_ = [max(self._min[i], other._min[i]) for i in xrange(3)]
        max_ = [min(self._max[i], other._max[i]) for i in xrange(3)]
        return BoundingBox(min_, max_)

    def collides(self, other, inclusive=[]):
        for i in xrange(3):
            if i in inclusive: func_suffix = 't'
            else: func_suffix = 'e'

            if getattr(self._max[i], '__l%s__' % func_suffix)(other._min[i]): return False
            if getattr(self._min[i], '__g%s__' % func_suffix)(other._max[i]): return False

        # same as the following but with inclusive check
        # if self._max.x <= other._min.x: return False # self is left of other
        # if self._min.x >= other._max.x: return False # self is right of other
        # if self._max.y <= other._min.y: return False # self is above other
        # if self._min.y >= other._max.y: return False # self is below other
        # if self._max.z <= other._min.z: return False # self is behind other
        # if self._min.z >= other._max.z: return False # self is in front of other

        return True # boxes overlap

    def translate(self, pos):
        bbox = self.copy()
        bbox._min += pos
        bbox._max += pos
        return bbox

