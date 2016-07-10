import functools
import types
import inspect

class EnableCachedMethods(type):
    """ This is a metaclass that, when used in conjunction with the
    `cached_method` function decorator, will create a method that just returns
    the cached result of the decorated method.

    The created method will be called by the decorator at runtime.
    See the docs for `cached_method` for more info.
    """
    def __new__(cls, name, bases, cls_dict):
        for obj_name, obj in cls_dict.items():
            if not inspect.isfunction(obj):
                continue
            if not getattr(obj, 'cached_method', False):
                continue

            code = inspect.cleandoc('''
                def _cached__%(func_name)s(self):
                    return self.%(cache_variable_name)s
            ''') % dict(func_name=obj_name, cache_variable_name=obj.cache_variable_name)
            exec code in cls_dict
        return type.__new__(cls, name, bases, cls_dict)

def cached_method(cache_variable_name):  # type: types.FunctionType
    """ This is a function decorator that, when used in conjunction with the
    `EnableCachedMethods` metaclass, sets up caching on a method so that
    subsequent calls to it will be faster.

    Requirements:
        - The method must have no arguments other than the `self` argument.

    Args:
        cache_variable_name (str):
            The name of the variable to use to cache the result of the method.

    Returns:
        types.FunctionType
    """
    # assert that this decorator was called with the appropriate arguments
    #
    assert isinstance(cache_variable_name, basestring), 'cached_method decorator expects 1 argument specifying the name of the cache variable'

    def wrapper(func):
        # assert that the function has the required argspec
        #
        argspec = inspect.getargspec(func)
        assert len(argspec.args) == 1 and argspec.args[0] == 'self', 'Invalid arg spec for decorated function.  Expected no arguments.'

        # Wrap `func` by:
        # - assigning the result to the variable named by `cache_variable_name`
        # - re-assigning func's name to a method that just returns the cache result.
        #   This method will be created by the `EnableCachedMethods` metaclass.
        # - returning the cached result
        code = inspect.cleandoc('''
            @functools.wraps(func)
            def wrapped(self):
                self.%(cache_variable_name)s = func(self)
                self.%(func_name)s = self._cached__%(func_name)s
                return self.%(cache_variable_name)s
        ''') % dict(cache_variable_name=cache_variable_name, func_name=func.__name__)
        wrapped_func_container = {
            'functools': functools,
            'func': func,
        }
        exec code in wrapped_func_container

        # Add some attributes to the wrapped function created above.
        # These attributes are required by the `EnableCachedMethods` metaclass
        # later so that it can create a method that just returns the cached result of `func`.
        #
        wrapped = wrapped_func_container['wrapped']
        wrapped.cached_method = True
        wrapped.cache_variable_name = cache_variable_name

        return wrapped
    return wrapper

