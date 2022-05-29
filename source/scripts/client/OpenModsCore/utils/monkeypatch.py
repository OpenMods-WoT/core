import inspect
from functools import partial, update_wrapper
from .abstract import redirect_traceback

__all__ = ('overrideMethod', 'find_attr', 'find_attr_name')
_sentinel = object()


def find_attr_name(obj, name, accept_property=False):
    if not name.endswith('__'):
        while name.startswith('_'):
            name = name[1:]
    full_name = '__'.join((getattr(obj, '__name__', obj.__class__.__name__), name))
    if not full_name.startswith('_'):
        full_name = '_' + full_name
    suf_name = '_' + name
    for _name in ((full_name, suf_name, name), (name, suf_name, full_name))[accept_property]:
        if hasattr(obj, _name):
            return _name


def find_attr(obj, name, default=_sentinel, accept_property=False):
    _name = find_attr_name(obj, name, accept_property)
    if _name is None and default is not _sentinel:
        return default
    return getattr(obj, (_name or ('_' + name)))


def overrideMethod(obj, prop=_sentinel, getter=None, setter=None, deleter=None):
    """
    :param obj: object, which attribute needs overriding
    :param prop: attribute name (can be not mangled), attribute must be callable
    :param getter: fget function or None
    :param setter: fset function or None
    :param deleter: fdel function or None
    :return function: unmodified getter or, if getter is None and src is not property, decorator"""

    if getter:
        getter_func = getter
        while isinstance(getter_func, partial):
            getter_func = getter_func.func
    if prop is _sentinel:
        if getter:
            # noinspection PyUnboundLocalVariable
            prop = getter_func.__name__
        else:
            return partial(overrideMethod, obj, prop)
    if inspect.isclass(obj) and not prop.endswith('__') and not hasattr(obj, prop):
        prop = find_attr_name(obj, prop, True)
    src = getattr(obj, prop)
    if type(src) is property and (getter or setter or deleter):
        props = []
        for func, fType in ((getter, 'fget'), (setter, 'fset'), (deleter, 'fdel')):
            assert func is None or callable(func), fType + ' is not callable!'
            props.append(partial(func, getattr(src, fType)) if func else getattr(src, fType))
        setattr(obj, prop, property(*props))
        return getter
    elif getter:
        assert callable(src), 'Source property is not callable!'
        assert callable(getter), 'Handler is not callable!'
        getter_new = redirect_traceback(partial(getter, src), getattr(getter_func, 'func_code', None))
        try:
            update_wrapper(getter_new, getter_func)
        except AttributeError:
            pass
        if inspect.isclass(obj):
            if inspect.isfunction(src):
                getter_new = staticmethod(getter_new)
            elif getattr(src, '__self__', None) is not None:
                getter_new = classmethod(getter_new)
        setattr(obj, prop, getter_new)
        return getter
    else:
        return partial(overrideMethod, obj, prop)
