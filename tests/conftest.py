# -*- coding: utf-8 -*-
"""
    tests.conftest
    ~~~~~~~~~~~~~~

    :copyright: (c) 2015 by the Flask Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import flask
import gc
import os
import sys
import pkgutil
import pytest
import textwrap


@pytest.fixture
def test_apps(monkeypatch):
    monkeypatch.syspath_prepend(
        os.path.abspath(os.path.join(
            os.path.dirname(__file__), 'test_apps'))
    )

@pytest.fixture(autouse=True)
def leak_detector(request):
    def ensure_clean_request_context():
        # make sure we're not leaking a request context since we are
        # testing flask internally in debug mode in a few cases
        leaks = []
        while flask._request_ctx_stack.top is not None:
            leaks.append(flask._request_ctx_stack.pop())
        assert leaks == []
    request.addfinalizer(ensure_clean_request_context)


@pytest.fixture(params=(True, False))
def limit_loader(request, monkeypatch):
    """Patch pkgutil.get_loader to give loader without get_filename or archive.

    This provides for tests where a system has custom loaders, e.g. Google App
    Engine's HardenedModulesHook, which have neither the `get_filename` method
    nor the `archive` attribute.

    This fixture will run the testcase twice, once with and once without the
    limitation/mock.
    """
    if not request.param:
        return

    class LimitedLoader(object):
        def __init__(self, loader):
            self.loader = loader

        def __getattr__(self, name):
            if name in ('archive', 'get_filename'):
                msg = 'Mocking a loader which does not have `%s.`' % name
                raise AttributeError(msg)
            return getattr(self.loader, name)

    old_get_loader = pkgutil.get_loader

    def get_loader(*args, **kwargs):
        return LimitedLoader(old_get_loader(*args, **kwargs))
    monkeypatch.setattr(pkgutil, 'get_loader', get_loader)


@pytest.fixture
def modules_tmpdir(tmpdir, monkeypatch):
    '''A tmpdir added to sys.path'''
    rv = tmpdir.mkdir('modules_tmpdir')
    monkeypatch.syspath_prepend(str(rv))
    return rv


@pytest.fixture
def modules_tmpdir_prefix(modules_tmpdir, monkeypatch):
    monkeypatch.setattr(sys, 'prefix', str(modules_tmpdir))
    return modules_tmpdir


@pytest.fixture
def site_packages(modules_tmpdir, monkeypatch):
    '''Create a fake site-packages'''
    rv = modules_tmpdir \
        .mkdir('lib')\
        .mkdir('python{x[0]}.{x[1]}'.format(x=sys.version_info))\
        .mkdir('site-packages')
    monkeypatch.syspath_prepend(str(rv))
    return rv


@pytest.fixture
def install_egg(modules_tmpdir, monkeypatch):
    '''Generate egg from package name inside base and put the egg into
    sys.path'''
    def inner(name, base=modules_tmpdir):
        if not isinstance(name, str):
            raise ValueError(name)
        base.join(name).ensure_dir()
        base.join(name).join('__init__.py').ensure()

        egg_setup = base.join('setup.py')
        egg_setup.write(textwrap.dedent("""
        from setuptools import setup
        setup(name='{0}',
              version='1.0',
              packages=['site_egg'],
              zip_safe=True)
        """.format(name)))

        import subprocess
        subprocess.check_call(
            [sys.executable, 'setup.py', 'bdist_egg'],
            cwd=str(modules_tmpdir)
        )
        egg_path, = modules_tmpdir.join('dist/').listdir()
        monkeypatch.syspath_prepend(str(egg_path))
        return egg_path
    return inner


@pytest.fixture
def purge_module(request):
    def inner(name):
        request.addfinalizer(lambda: sys.modules.pop(name, None))
    return inner


@pytest.yield_fixture(autouse=True)
def catch_deprecation_warnings(recwarn):
    yield
    gc.collect()
    assert not recwarn.list
