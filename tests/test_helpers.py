import io
import os

import pytest
import werkzeug.exceptions

import flask
from flask.helpers import get_debug_flag


class FakePath:
    """Fake object to represent a ``PathLike object``.

    This represents a ``pathlib.Path`` object in python 3.
    See: https://www.python.org/dev/peps/pep-0519/
    """

    def __init__(self, path):
        self.path = path

    def __fspath__(self):
        return self.path


class PyBytesIO:
    def __init__(self, *args, **kwargs):
        self._io = io.BytesIO(*args, **kwargs)

    def __getattr__(self, name):
        return getattr(self._io, name)


class TestSendfile:
    def test_send_file(self, app, req_ctx):
        rv = flask.send_file("static/index.html")
        assert rv.direct_passthrough
        assert rv.mimetype == "text/html"

        with app.open_resource("static/index.html") as f:
            rv.direct_passthrough = False
            assert rv.data == f.read()

        rv.close()

    def test_static_file(self, app, req_ctx):
        # Default max_age is None.

        # Test with static file handler.
        rv = app.send_static_file("index.html")
        assert rv.cache_control.max_age is None
        rv.close()

        # Test with direct use of send_file.
        rv = flask.send_file("static/index.html")
        assert rv.cache_control.max_age is None
        rv.close()

        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600

        # Test with static file handler.
        rv = app.send_static_file("index.html")
        assert rv.cache_control.max_age == 3600
        rv.close()

        # Test with direct use of send_file.
        rv = flask.send_file("static/index.html")
        assert rv.cache_control.max_age == 3600
        rv.close()

        # Test with pathlib.Path.
        rv = app.send_static_file(FakePath("index.html"))
        assert rv.cache_control.max_age == 3600
        rv.close()

        class StaticFileApp(flask.Flask):
            def get_send_file_max_age(self, filename):
                return 10

        app = StaticFileApp(__name__)

        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file("index.html")
            assert rv.cache_control.max_age == 10
            rv.close()

            # Test with direct use of send_file.
            rv = flask.send_file("static/index.html")
            assert rv.cache_control.max_age == 10
            rv.close()

    def test_send_from_directory(self, app, req_ctx):
        app.root_path = os.path.join(
            os.path.dirname(__file__), "test_apps", "subdomaintestmodule"
        )
        rv = flask.send_from_directory("static", "hello.txt")
        rv.direct_passthrough = False
        assert rv.data.strip() == b"Hello Subdomain"
        rv.close()


class TestUrlFor:
    def test_url_for_with_anchor(self, app, req_ctx):
        @app.route("/")
        def index():
            return "42"

        assert flask.url_for("index", _anchor="x y") == "/#x%20y"

    def test_url_for_with_scheme(self, app, req_ctx):
        @app.route("/")
        def index():
            return "42"

        assert (
            flask.url_for("index", _external=True, _scheme="https")
            == "https://localhost/"
        )

    def test_url_for_with_scheme_not_external(self, app, req_ctx):
        app.add_url_rule("/", endpoint="index")

        # Implicit external with scheme.
        url = flask.url_for("index", _scheme="https")
        assert url == "https://localhost/"

        # Error when external=False with scheme
        with pytest.raises(ValueError):
            flask.url_for("index", _scheme="https", _external=False)

    def test_url_for_with_alternating_schemes(self, app, req_ctx):
        @app.route("/")
        def index():
            return "42"

        assert flask.url_for("index", _external=True) == "http://localhost/"
        assert (
            flask.url_for("index", _external=True, _scheme="https")
            == "https://localhost/"
        )
        assert flask.url_for("index", _external=True) == "http://localhost/"

    def test_url_with_method(self, app, req_ctx):
        from flask.views import MethodView

        class MyView(MethodView):
            def get(self, id=None):
                if id is None:
                    return "List"
                return f"Get {id:d}"

            def post(self):
                return "Create"

        myview = MyView.as_view("myview")
        app.add_url_rule("/myview/", methods=["GET"], view_func=myview)
        app.add_url_rule("/myview/<int:id>", methods=["GET"], view_func=myview)
        app.add_url_rule("/myview/create", methods=["POST"], view_func=myview)

        assert flask.url_for("myview", _method="GET") == "/myview/"
        assert flask.url_for("myview", id=42, _method="GET") == "/myview/42"
        assert flask.url_for("myview", _method="POST") == "/myview/create"

    def test_url_for_with_self(self, app, req_ctx):
        @app.route("/<self>")
        def index(self):
            return "42"

        assert flask.url_for("index", self="2") == "/2"


def test_redirect_no_app():
    response = flask.redirect("https://localhost", 307)
    assert response.location == "https://localhost"
    assert response.status_code == 307


def test_redirect_with_app(app):
    def redirect(location, code=302):
        raise ValueError

    app.redirect = redirect

    with app.app_context(), pytest.raises(ValueError):
        flask.redirect("other")


def test_abort_no_app():
    with pytest.raises(werkzeug.exceptions.Unauthorized):
        flask.abort(401)

    with pytest.raises(LookupError):
        flask.abort(900)


def test_app_aborter_class():
    class MyAborter(werkzeug.exceptions.Aborter):
        pass

    class MyFlask(flask.Flask):
        aborter_class = MyAborter

    app = MyFlask(__name__)
    assert isinstance(app.aborter, MyAborter)


def test_abort_with_app(app):
    class My900Error(werkzeug.exceptions.HTTPException):
        code = 900

    app.aborter.mapping[900] = My900Error

    with app.app_context(), pytest.raises(My900Error):
        flask.abort(900)


class TestNoImports:
    """Test Flasks are created without import.

    Avoiding ``__import__`` helps create Flask instances where there are errors
    at import time.  Those runtime errors will be apparent to the user soon
    enough, but tools which build Flask instances meta-programmatically benefit
    from a Flask which does not ``__import__``.  Instead of importing to
    retrieve file paths or metadata on a module or package, use the pkgutil and
    imp modules in the Python standard library.
    """

    def test_name_with_import_error(self, modules_tmp_path):
        (modules_tmp_path / "importerror.py").write_text("raise NotImplementedError()")
        try:
            flask.Flask("importerror")
        except NotImplementedError:
            AssertionError("Flask(import_name) is importing import_name.")


class TestStreaming:
    def test_streaming_with_context(self, app, client):
        @app.route("/")
        def index():
            def generate():
                yield "Hello "
                yield flask.request.args["name"]
                yield "!"

            return flask.Response(flask.stream_with_context(generate()))

        rv = client.get("/?name=World")
        assert rv.data == b"Hello World!"

    def test_streaming_with_context_as_decorator(self, app, client):
        @app.route("/")
        def index():
            @flask.stream_with_context
            def generate(hello):
                yield hello
                yield flask.request.args["name"]
                yield "!"

            return flask.Response(generate("Hello "))

        rv = client.get("/?name=World")
        assert rv.data == b"Hello World!"

    def test_streaming_with_context_and_custom_close(self, app, client):
        called = []

        class Wrapper:
            def __init__(self, gen):
                self._gen = gen

            def __iter__(self):
                return self

            def close(self):
                called.append(42)

            def __next__(self):
                return next(self._gen)

            next = __next__

        @app.route("/")
        def index():
            def generate():
                yield "Hello "
                yield flask.request.args["name"]
                yield "!"

            return flask.Response(flask.stream_with_context(Wrapper(generate())))

        rv = client.get("/?name=World")
        assert rv.data == b"Hello World!"
        assert called == [42]

    def test_stream_keeps_session(self, app, client):
        @app.route("/")
        def index():
            flask.session["test"] = "flask"

            @flask.stream_with_context
            def gen():
                yield flask.session["test"]

            return flask.Response(gen())

        rv = client.get("/")
        assert rv.data == b"flask"


class TestHelpers:
    @pytest.mark.parametrize(
        ("debug", "expect"),
        [
            ("", False),
            ("0", False),
            ("False", False),
            ("No", False),
            ("True", True),
        ],
    )
    def test_get_debug_flag(self, monkeypatch, debug, expect):
        monkeypatch.setenv("FLASK_DEBUG", debug)
        assert get_debug_flag() == expect

    def test_make_response(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.helpers.make_response()
            assert rv.status_code == 200
            assert rv.mimetype == "text/html"

            rv = flask.helpers.make_response("Hello")
            assert rv.status_code == 200
            assert rv.data == b"Hello"
            assert rv.mimetype == "text/html"


@pytest.mark.parametrize("mode", ("r", "rb", "rt"))
def test_open_resource(mode):
    app = flask.Flask(__name__)

    with app.open_resource("static/index.html", mode) as f:
        assert "<h1>Hello World!</h1>" in str(f.read())


@pytest.mark.parametrize("mode", ("w", "x", "a", "r+"))
def test_open_resource_exceptions(mode):
    app = flask.Flask(__name__)

    with pytest.raises(ValueError):
        app.open_resource("static/index.html", mode)


@pytest.mark.parametrize("encoding", ("utf-8", "utf-16-le"))
def test_open_resource_with_encoding(tmp_path, encoding):
    app = flask.Flask(__name__, root_path=os.fspath(tmp_path))
    (tmp_path / "test").write_text("test", encoding=encoding)

    with app.open_resource("test", mode="rt", encoding=encoding) as f:
        assert f.read() == "test"
