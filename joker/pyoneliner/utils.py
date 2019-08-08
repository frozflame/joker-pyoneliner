#!/usr/bin/env python3
# coding: utf-8


class Dot(object):
    result = None

    def __getattr__(self, name):
        return self

    def __call__(self, *args, **kwargs):
        return self

    def import_module(self, name):
        import importlib
        try:
            return importlib.import_module(name)
        except ImportError:
            return self


class FunctionWrapper(object):
    __slots__ = ['func']

    def __init__(self, func):
        self.func = func

    def __call__(self, *args, **kwargs):
        return self.func(*args, **kwargs)

    def __ror__(self, other):
        return self.func(other)

    def __getattr__(self, name):
        return getattr(self.func, name)

    @classmethod
    def wrap(cls, obj):
        if callable(obj) and not isinstance(obj, cls):
            return cls(obj)
        return obj

    @classmethod
    def wrap_attributes(cls, *modules):
        rd = {}
        for m in modules:
            names = (n for n in dir(m) if not n.startswith('_'))
            rd.update({n: cls.wrap(getattr(m, n)) for n in names})
        return rd


class ModuleWrapper(object):
    __slots__ = ['_vmod_ctx', '_vmod_dot', '_vmod_mod', '_vmod_name']

    def __init__(self, name=None, ctx=None):
        self._vmod_ctx = ctx or {}
        self._vmod_dot = Dot()
        self._vmod_mod = None
        self._vmod_name = name

    def _vmod_getattr(self, name):
        if name in self._vmod_ctx:
            return self._vmod_ctx[name]
        if not self._vmod_name:
            return ModuleWrapper(name)
        if self._vmod_mod is None:
            self._vmod_mod = self._vmod_dot.import_module(self._vmod_name)
        try:
            return getattr(self._vmod_mod, name)
        except AttributeError:
            prefix = self._vmod_name + '.' if self._vmod_name else ''
            return ModuleWrapper(prefix + name)

    def __getattr__(self, name):
        rv = self._vmod_getattr(name)
        passby_types = ModuleWrapper, FunctionWrapper
        if not isinstance(rv, passby_types) and callable(rv):
            return FunctionWrapper(rv)
        return rv


def prints(iterable, *args, **kwargs):
    for line in iterable:
        print(line, *args, **kwargs)


def printer(*args, **kwargs):
    return FunctionWrapper(lambda iterable: prints(iterable, *args, **kwargs))


