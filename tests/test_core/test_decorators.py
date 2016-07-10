import pytest
from tempest.core import decorators

def test_cached_method():
    # assert that the cached_method decorator errors if no arguments are passed in
    with pytest.raises(AssertionError):
        class FailureClass(object):
            __metaclass__ = decorators.EnableCachedMethods

            @decorators.cached_method
            def failure_method(self):
                pass

    class Foo(object):
        __metaclass__ = decorators.EnableCachedMethods

        count = 0

        @decorators.cached_method('_cached_method_result')
        def cached_method(self):
            Foo.count += 1
            return Foo.count

    inst1 = Foo()
    inst2 = Foo()
    assert inst1.cached_method() == inst1.cached_method()
    assert inst2.cached_method() == inst2.cached_method()
    assert inst1.cached_method() != inst2.cached_method()

    assert hasattr(inst1, '_cached_method_result')
    assert inst1._cached_method_result == 1
    assert inst1.cached_method.__name__ == '_cached__cached_method'

