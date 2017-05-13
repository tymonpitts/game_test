import pytest
from game_core import decorators

def test_cached_method():
    # assert that the cached_method decorator errors if the decorated method has arguments
    with pytest.raises(AssertionError):
        class FailureClass(object):
            __metaclass__ = decorators.EnableCachedMethods

            @decorators.cached_method
            def failure_method(self, unexpected_arg):
                pass

    class Foo(object):
        __metaclass__ = decorators.EnableCachedMethods

        count = 0

        @decorators.cached_method
        def bar(self):
            Foo.count += 1
            return Foo.count

    assert hasattr(Foo, '_bar__cached')

    inst1 = Foo()
    inst2 = Foo()
    assert inst1.bar() == inst1.bar()
    assert inst2.bar() == inst2.bar()
    assert inst1.bar() != inst2.bar()

    assert hasattr(inst1, '_bar__result')
    assert inst1._bar__result == 1
    assert inst1.bar.__name__ == '_bar__cached'

