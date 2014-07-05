from collections import OrderedDict

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
    def __init__(self, id):
        super(AbstractBlock, self).__setattr__('_attributes', self.attributes())
        state = self._ID_TO_STATE[id]
        for name, value in state.iteritems():
            setattr(self, name, value)

    def __setattr__(self, name, value):
        if name in self._attributes:
            if value not in self._attributes[name]:
                raise ValueError('%s is not a valid value for "%s".  Valid values are: %s' % (value, name, values))
        super(AbstractBlock, self).__setattr__(name, value)

    @classmethod
    def from_state(cls, state):
        state_id = None
        for id, id_state in cls._ID_TO_STATE.iteritems():
            if id_state == state:
                state_id = id
        if state_id is None:
            raise ValueError('The specified state does not exist: %s' % state)
        return cls(state_id)

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
        # result = {}
        # result['test'] = range(10)
        # return result

class Air(AbstractBlock):
    pass

class Rock(AbstractBlock):
    TopConnected    = int('000001', 2)
    BottomConnected = int('000010', 2)
    RightConnected  = int('000100', 2)
    LeftConnected   = int('001000', 2)
    FrontConnected  = int('010000', 2)
    BackConnected   = int('100000', 2)
    @classmethod
    def attributes(cls):
        result = OrderedDict()
        result['connected'] = reversed(range(int('111111', 2)))
        return result
