
import argparse
import pkgutil
import importlib

import pytest

import bench

implementations = []
for modinfo in pkgutil.iter_modules(bench.__path__):
    if modinfo.ispkg:
        implementations.append(modinfo.name)


def _csvtype(choices):

    def splitarg(arg):
        values = arg.split(',')
        for value in values:
            if value not in choices:
                raise argparse.ArgumentTypeError(
                    'invalid choice: {!r} (choose from {})'
                    .format(value, ', '.join(map(repr, choices))))
        return values

    return splitarg


def pytest_addoption(parser):
    parser.addoption(
        '--bench',
        metavar='NAMES',
        type=_csvtype(implementations),
        help='comma-separated list of implementations to use')


def _skip_missing(*args, **kwargs):
    pytest.skip('not implemented')


def _get_funcs(libs, task, fixturename):
    funcs = []
    for lib in libs:
        try:
            mod = importlib.import_module(f'bench.{lib}.{task}')
        except ImportError:
            funcs.append(_skip_missing)
        else:
            funcs.append(getattr(mod, fixturename, _skip_missing))
    return funcs


def pytest_generate_tests(metafunc):
    libs = metafunc.config.getoption('--bench')
    if not libs:
        libs = implementations

    task = metafunc.module.TASK

    for fixturename in ('parse', 'compile'):
        if fixturename in metafunc.fixturenames:
            funcs = _get_funcs(libs, task, fixturename)
            metafunc.parametrize(fixturename, funcs, ids=libs)
