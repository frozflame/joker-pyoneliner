#!/usr/bin/env python3
# coding: utf-8

import builtins
import math
import os
import sys

from joker.pyoneliner import utils


def _report(obj, use_repr=False, use_prints=False, **kwargs):
    func = utils.prints if use_prints else print
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

    wa = utils.FunctionWrapper.wrap_attributes
    ctx = wa(os, os.path, sys, str, builtins, math)
    ctx['prints'] = utils.prints
    ctx['printer'] = utils.printer

    ol = utils.ModuleWrapper('', ctx)
    ctx_global = {
        'ol': ol,
        'sys': sys,
        'stdin': ShellStream(sys.stdin),
        'stdout': ShellStream(sys.stdout),
        'stderr': ShellStream(sys.stderr),
        'os': os,
        'math': math,
        're': utils.ModuleWrapper('re'),
        'np': utils.ModuleWrapper('numpy'),
        'args': arguments,
        'prints': ol.prints,
        'printer': ol.puts,
        'wrapf': utils.FunctionWrapper,
    }
    for i, v in enumerate(arguments):
        k = 'a{}'.format(i)
        ctx_global[k] = v
    for i in range(8):
        k = 'a{}'.format(i)
        ctx_global.setdefault(k, None)
    return ctx_global


def hook(result):
    utils.Dot.result = result


def olexec(text, ctx):
    code = compile(text.strip(), '-', 'single')
    sys.displayhook = hook
    exec(code, ctx)
    return utils.Dot.result


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
