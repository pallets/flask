import os
import pkgutil
import sys
import textwrap

import pytest
from _pytest import monkeypatch

import flask
from flask import Flask as _Flask


@pytest.fixture(scope="session", autouse=True)
def _standard_os_environ():
    """Set up ``os.environ`` at the start of the test session to have
    standard values. Returns a list of operations that is used by
    :func:`._reset_os_environ` after each test.
    """
    mp = monkeypatch.MonkeyPatch()
    out = (
        (os.environ, "FLASK_APP", monkeypatch.notset),
        (os.environ, "FLASK_ENV", monkeypatch.notset),
        (os.environ, "FLASK_DEBUG", monkeypatch.notset),
        (os.environ, "FLASK_RUN_FROM_CLI", monkeypatch.notset),
        (os.environ, "WERKZEUG_RUN_MAIN", monkeypatch.notset),
    )

    for _, key, value in out:
        if value is monkeypatch.notset:
            mp.delenv(key, False)
        else:
            mp.setenv(key, value)

    yield out
    mp.undo()


@pytest.fixture(autouse=True)
def _reset_os_environ(monkeypatch, _standard_os_environ):
    """Reset ``os.environ`` to the standard environ after each test,
    in case a test changed something without cleaning up.
    """
    monkeypatch._setitem.extend(_standard_os_environ)


class Flask(_Flask):
    testing = True
    secret_key = "test key"


@pytest.fixture
def app():
    app = Flask("flask_test", root_path=os.path.dirname(__file__))
    return app


@pytest.fixture
def app_ctx(app):
    with app.app_context() as ctx:
        yield ctx


@pytest.fixture
def req_ctx(app):
    with app.test_request_context() as ctx:
        yield ctx


@pytest.fixture
def client(app):
    return app.test_client()


@pytest.fixture
def test_apps(monkeypatch):
    monkeypatch.syspath_prepend(os.path.join(os.path.dirname(__file__), "test_apps"))
    original_modules = set(sys.modules.keys())

    yield

    # Remove any imports cached during the test. Otherwise "import app"
    # will work in the next test even though it's no longer on the path.
    for key in sys.modules.keys() - original_modules:
        sys.modules.pop(key)


@pytest.fixture(autouse=True)
def leak_detector():
    yield

    # make sure we're not leaking a request context since we are
    # testing flask internally in debug mode in a few cases
    leaks = []
    while flask._request_ctx_stack.top is not None:
        leaks.append(flask._request_ctx_stack.pop())
    assert leaks == []


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

    class LimitedLoader:
        def __init__(self, loader):
            self.loader = loader

        def __getattr__(self, name):
            if name in {"archive", "get_filename"}:
                raise AttributeError(f"Mocking a loader which does not have {name!r}.")
            return getattr(self.loader, name)

    old_get_loader = pkgutil.get_loader

    def get_loader(*args, **kwargs):
        return LimitedLoader(old_get_loader(*args, **kwargs))

    monkeypatch.setattr(pkgutil, "get_loader", get_loader)


@pytest.fixture
def modules_tmpdir(tmpdir, monkeypatch):
    """A tmpdir added to sys.path."""
    rv = tmpdir.mkdir("modules_tmpdir")
    monkeypatch.syspath_prepend(str(rv))
    return rv


@pytest.fixture
def modules_tmpdir_prefix(modules_tmpdir, monkeypatch):
    monkeypatch.setattr(sys, "prefix", str(modules_tmpdir))
    return modules_tmpdir


@pytest.fixture
def site_packages(modules_tmpdir, monkeypatch):
    """Create a fake site-packages."""
    rv = (
        modules_tmpdir.mkdir("lib")
        .mkdir(f"python{sys.version_info.major}.{sys.version_info.minor}")
        .mkdir("site-packages")
    )
    monkeypatch.syspath_prepend(str(rv))
    return rv


@pytest.fixture
def install_egg(modules_tmpdir, monkeypatch):
    """Generate egg from package name inside base and put the egg into
    sys.path."""

    def inner(name, base=modules_tmpdir):
        base.join(name).ensure_dir()
        base.join(name).join("__init__.py").ensure()

        egg_setup = base.join("setup.py")
        egg_setup.write(
            textwrap.dedent(
                f"""
                from setuptools import setup
                setup(
                    name="{name}",
                    version="1.0",
                    packages=["site_egg"],
                    zip_safe=True,
                )
                """
            )
        )

        import subprocess

        subprocess.check_call(
            [sys.executable, "setup.py", "bdist_egg"], cwd=str(modules_tmpdir)
        )
        (egg_path,) = modules_tmpdir.join("dist/").listdir()
        monkeypatch.syspath_prepend(str(egg_path))
        return egg_path

    return inner


@pytest.fixture
def purge_module(request):
    def inner(name):
        request.addfinalizer(lambda: sys.modules.pop(name, None))

    return inner
