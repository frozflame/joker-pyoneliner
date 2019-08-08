#!/usr/bin/env python3
# coding: utf-8

import builtins
import os
import sys
import math


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


def _report(obj, use_repr=False, use_prints=False, **kwargs):
    func = prints if use_prints else print
    if use_repr:
        if use_prints:
            obj = (repr(o) for o in obj)
        else:
            obj = repr(obj)
    func(obj, **kwargs)


def get_global_context(arguments, argnumerify=False):
    from joker.stream.shell import ShellStream
    if argnumerify:
        from joker.cast import numerify
        arguments = [numerify(x) for x in arguments]

    wa = FunctionWrapper.wrap_attributes
    ctx = wa(os, os.path, sys, str, builtins, math)
    ctx['prints'] = prints
    ctx['printer'] = printer

    ol = ModuleWrapper('', ctx)
    ctx_global = {
        'ol': ol,
        'sys': sys,
        'stdin': ShellStream(sys.stdin),
        'stdout': ShellStream(sys.stdout),
        'stderr': ShellStream(sys.stderr),
        'os': os,
        'math': math,
        're': ModuleWrapper('re'),
        'np': ModuleWrapper('numpy'),
        'args': arguments,
        'prints': ol.prints,
        'printer': ol.puts,
        'wrapf': FunctionWrapper,
    }
    for i, v in enumerate(arguments):
        k = 'a{}'.format(i)
        ctx_global[k] = v
    for i in range(8):
        k = 'a{}'.format(i)
        ctx_global.setdefault(k, None)
    return ctx_global


def hook(result):
    Dot.result = result


def olexec(text, ctx):
    code = compile(text.strip(), '-', 'single')
    sys.displayhook = hook
    exec(code, ctx)
    return Dot.result


def run(prog=None, args=None):
    import argparse
    import sys
    if not prog and sys.argv[0].endswith('__main__.py'):
        prog = 'python3 -m joker.pyoneliner'
    desc = 'python one-liners in an easier way'
    pr = argparse.ArgumentParser(prog=prog, description=desc)
    aa = pr.add_argument
    aa('-n', '--numerify', action='store_true',
       help='convert values to int/float if possible')
    aa('-r', '--repr', action='store_true',
       help='print repr() of the final result')
    aa('-s', '--prints', action='store_true',
       help='show final result with prints()')
    aa('code', help='python statements separated by ";"')
    aa('argument', nargs='*', help='a[0-9]+ and args in code')
    ns = pr.parse_args(args)
    arguments = [ns.code] + ns.argument
    ctx = get_global_context(arguments, ns.numerify)
    rv = olexec(ns.code, ctx)
    if rv is not None:
        _report(rv, use_prints=ns.prints, use_repr=ns.repr)
