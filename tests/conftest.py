import os
import sys

import pytest

from flask import Flask
from flask.globals import app_ctx as _app_ctx

_standard_env_keys = (
    "FLASK_ENV_FILE",
    "FLASK_APP",
    "FLASK_DEBUG",
    "FLASK_RUN_FROM_CLI",
    "WERKZEUG_RUN_MAIN",
)

# Env vars used by dotenv tests that may be set by load_dotenv() directly
# (bypassing monkeypatch), so they need explicit cleanup between tests.
_dotenv_test_keys = (
    "FOO",
    "BAR",
    "SPAM",
    "HAM",
    "EGGS",
)


@pytest.fixture(scope="session", autouse=True)
def _standard_os_environ():
    """Set up ``os.environ`` at the start of the test session to have
    standard values.
    """
    mp = pytest.MonkeyPatch()
    for key in _standard_env_keys:
        mp.delenv(key, raising=False)

    yield
    mp.undo()


@pytest.fixture(autouse=True)
def _reset_os_environ(monkeypatch):
    """Reset ``os.environ`` to the standard environ after each test,
    in case a test changed something without cleaning up.
    """
    for key in _standard_env_keys:
        monkeypatch.delenv(key, raising=False)
    for key in _dotenv_test_keys:
        monkeypatch.delenv(key, raising=False)


@pytest.fixture
def app():
    app = Flask("flask_test", root_path=os.path.dirname(__file__))
    app.config.update(
        TESTING=True,
        SECRET_KEY="test key",
    )
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
    """Fails if any app contexts are still pushed when a test ends. Pops all
    contexts so subsequent tests are not affected.
    """
    yield
    leaks = []

    while _app_ctx:
        leaks.append(_app_ctx._get_current_object())
        _app_ctx.pop()

    assert not leaks


@pytest.fixture
def modules_tmp_path(tmp_path, monkeypatch):
    """A temporary directory added to sys.path."""
    rv = tmp_path / "modules_tmp"
    rv.mkdir()
    monkeypatch.syspath_prepend(os.fspath(rv))
    return rv


@pytest.fixture
def modules_tmp_path_prefix(modules_tmp_path, monkeypatch):
    monkeypatch.setattr(sys, "prefix", os.fspath(modules_tmp_path))
    return modules_tmp_path


@pytest.fixture
def site_packages(modules_tmp_path, monkeypatch):
    """Create a fake site-packages."""
    py_dir = f"python{sys.version_info.major}.{sys.version_info.minor}"
    rv = modules_tmp_path / "lib" / py_dir / "site-packages"
    rv.mkdir(parents=True)
    monkeypatch.syspath_prepend(os.fspath(rv))
    return rv


@pytest.fixture
def purge_module(request):
    def inner(name):
        request.addfinalizer(lambda: sys.modules.pop(name, None))

    return inner
