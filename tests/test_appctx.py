import sys

import pytest

import flask
from flask.globals import app_ctx
from flask.testing import FlaskClient


def test_basic_url_generation(app):
    app.config["SERVER_NAME"] = "localhost"
    app.config["PREFERRED_URL_SCHEME"] = "https"

    @app.route("/")
    def index():
        pass

    with app.app_context():
        rv = flask.url_for("index")
        assert rv == "https://localhost/"


def test_url_generation_requires_server_name(app):
    with app.app_context():
        with pytest.raises(RuntimeError):
            flask.url_for("index")


def test_url_generation_without_context_fails():
    with pytest.raises(RuntimeError):
        flask.url_for("index")


def test_request_context_means_app_context(app):
    with app.test_request_context():
        assert flask.current_app._get_current_object() is app
    assert not flask.current_app


def test_app_context_provides_current_app(app):
    with app.app_context():
        assert flask.current_app._get_current_object() is app
    assert not flask.current_app


def test_app_tearing_down(app):
    cleanup_stuff = []

    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    with app.app_context():
        pass

    assert cleanup_stuff == [None]


def test_app_tearing_down_with_previous_exception(app):
    cleanup_stuff = []

    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    try:
        raise Exception("dummy")
    except Exception:
        pass

    with app.app_context():
        pass

    assert cleanup_stuff == [None]


def test_app_tearing_down_with_handled_exception_by_except_block(app):
    cleanup_stuff = []

    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    with app.app_context():
        try:
            raise Exception("dummy")
        except Exception:
            pass

    assert cleanup_stuff == [None]


def test_app_tearing_down_with_handled_exception_by_app_handler(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = True
    cleanup_stuff = []

    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    @app.route("/")
    def index():
        raise Exception("dummy")

    @app.errorhandler(Exception)
    def handler(f):
        return flask.jsonify(str(f))

    with app.app_context():
        client.get("/")

    # teardown request context, and with block context
    assert cleanup_stuff == [None, None]


def test_app_tearing_down_with_unhandled_exception(app, client):
    app.config["PROPAGATE_EXCEPTIONS"] = True
    cleanup_stuff = []

    @app.teardown_appcontext
    def cleanup(exception):
        cleanup_stuff.append(exception)

    @app.route("/")
    def index():
        raise ValueError("dummy")

    with pytest.raises(ValueError, match="dummy"):
        with app.app_context():
            client.get("/")

    assert len(cleanup_stuff) == 2
    assert isinstance(cleanup_stuff[0], ValueError)
    assert str(cleanup_stuff[0]) == "dummy"
    # exception propagated, seen by request context and with block context
    assert cleanup_stuff[0] is cleanup_stuff[1]


def test_app_ctx_globals_methods(app, app_ctx):
    # get
    assert flask.g.get("foo") is None
    assert flask.g.get("foo", "bar") == "bar"
    # __contains__
    assert "foo" not in flask.g
    flask.g.foo = "bar"
    assert "foo" in flask.g
    # setdefault
    flask.g.setdefault("bar", "the cake is a lie")
    flask.g.setdefault("bar", "hello world")
    assert flask.g.bar == "the cake is a lie"
    # pop
    assert flask.g.pop("bar") == "the cake is a lie"
    with pytest.raises(KeyError):
        flask.g.pop("bar")
    assert flask.g.pop("bar", "more cake") == "more cake"
    # __iter__
    assert list(flask.g) == ["foo"]
    # __repr__
    assert repr(flask.g) == "<flask.g of 'flask_test'>"


def test_custom_app_ctx_globals_class(app):
    class CustomRequestGlobals:
        def __init__(self):
            self.spam = "eggs"

    app.app_ctx_globals_class = CustomRequestGlobals
    with app.app_context():
        assert flask.render_template_string("{{ g.spam }}") == "eggs"


def test_context_refcounts(app, client):
    called = []

    @app.teardown_request
    def teardown_req(error=None):
        called.append("request")

    @app.teardown_appcontext
    def teardown_app(error=None):
        called.append("app")

    @app.route("/")
    def index():
        with app_ctx:
            pass

        assert flask.request.environ["werkzeug.request"] is not None
        return ""

    res = client.get("/")
    assert res.status_code == 200
    assert res.data == b""
    assert called == ["request", "app"]


def test_clean_pop(app):
    app.testing = False
    called = []

    @app.teardown_request
    def teardown_req(error=None):
        raise ZeroDivisionError

    @app.teardown_appcontext
    def teardown_app(error=None):
        called.append("TEARDOWN")

    with app.app_context():
        called.append(flask.current_app.name)

    assert called == ["flask_test", "TEARDOWN"]
    assert not flask.current_app


def test_robust_teardown(app: flask.Flask, client: FlaskClient) -> None:
    count = 0

    @app.teardown_request
    def request_teardown(e: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("request_teardown")

    @app.teardown_appcontext
    def app_teardown(e: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("app_teardown")

    @app.get("/")
    def index() -> str:
        return ""

    def request_signal(sender: flask.Flask, exc: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("request_signal")

    def app_signal(sender: flask.Flask, exc: Exception | None) -> None:
        nonlocal count
        count += 1
        raise ValueError("app_signal")

    with (
        flask.request_tearing_down.connected_to(request_signal, app),
        flask.appcontext_tearing_down.connected_to(app_signal, app),
    ):
        if sys.version_info >= (3, 11):
            with pytest.raises(ExceptionGroup, match="context teardown") as exc_info:  # noqa: F821
                client.get()

            assert len(exc_info.value.exceptions) == 2
            eg1, eg2 = exc_info.value.exceptions
            assert isinstance(eg1, ExceptionGroup)  # noqa: F821
            assert "request teardown" in eg1.message
            assert len(eg1.exceptions) == 2
            assert isinstance(eg2, ExceptionGroup)  # noqa: F821
            assert "app teardown" in eg2.message
            assert len(eg2.exceptions) == 2
        else:
            with pytest.raises(ValueError, match="request_teardown"):
                client.get()

    assert count == 4
