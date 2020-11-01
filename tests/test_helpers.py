import datetime
import io
import os
import sys

import pytest
from werkzeug.datastructures import Range
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound
from werkzeug.http import http_date
from werkzeug.http import parse_cache_control_header
from werkzeug.http import parse_options_header

import flask
from flask.helpers import get_debug_flag
from flask.helpers import get_env


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
    def test_send_file_regular(self, app, req_ctx):
        rv = flask.send_file("static/index.html")
        assert rv.direct_passthrough
        assert rv.mimetype == "text/html"
        with app.open_resource("static/index.html") as f:
            rv.direct_passthrough = False
            assert rv.data == f.read()
        rv.close()

    def test_send_file_xsendfile(self, app, req_ctx):
        app.use_x_sendfile = True
        rv = flask.send_file("static/index.html")
        assert rv.direct_passthrough
        assert "x-sendfile" in rv.headers
        assert rv.headers["x-sendfile"] == os.path.join(
            app.root_path, "static/index.html"
        )
        assert rv.mimetype == "text/html"
        rv.close()

    def test_send_file_last_modified(self, app, client):
        last_modified = datetime.datetime(1999, 1, 1)

        @app.route("/")
        def index():
            return flask.send_file(
                io.BytesIO(b"party like it's"),
                last_modified=last_modified,
                mimetype="text/plain",
            )

        rv = client.get("/")
        assert rv.last_modified == last_modified

    def test_send_file_object_without_mimetype(self, app, req_ctx):
        with pytest.raises(ValueError) as excinfo:
            flask.send_file(io.BytesIO(b"LOL"))
        assert "Unable to infer MIME-type" in str(excinfo.value)
        assert "no filename is available" in str(excinfo.value)

        flask.send_file(io.BytesIO(b"LOL"), attachment_filename="filename")

    @pytest.mark.parametrize(
        "opener",
        [
            lambda app: open(os.path.join(app.static_folder, "index.html"), "rb"),
            lambda app: io.BytesIO(b"Test"),
            lambda app: PyBytesIO(b"Test"),
        ],
    )
    @pytest.mark.usefixtures("req_ctx")
    def test_send_file_object(self, app, opener):
        file = opener(app)
        app.use_x_sendfile = True
        rv = flask.send_file(file, mimetype="text/plain")
        rv.direct_passthrough = False
        assert rv.data
        assert rv.mimetype == "text/plain"
        assert "x-sendfile" not in rv.headers
        rv.close()

    @pytest.mark.parametrize(
        "opener",
        [
            lambda app: io.StringIO("Test"),
            lambda app: open(os.path.join(app.static_folder, "index.html")),
        ],
    )
    @pytest.mark.usefixtures("req_ctx")
    def test_send_file_text_fails(self, app, opener):
        file = opener(app)

        with pytest.raises(ValueError):
            flask.send_file(file, mimetype="text/plain")

        file.close()

    def test_send_file_pathlike(self, app, req_ctx):
        rv = flask.send_file(FakePath("static/index.html"))
        assert rv.direct_passthrough
        assert rv.mimetype == "text/html"
        with app.open_resource("static/index.html") as f:
            rv.direct_passthrough = False
            assert rv.data == f.read()
        rv.close()

    @pytest.mark.skipif(
        not callable(getattr(Range, "to_content_range_header", None)),
        reason="not implemented within werkzeug",
    )
    def test_send_file_range_request(self, app, client):
        @app.route("/")
        def index():
            return flask.send_file("static/index.html", conditional=True)

        rv = client.get("/", headers={"Range": "bytes=4-15"})
        assert rv.status_code == 206
        with app.open_resource("static/index.html") as f:
            assert rv.data == f.read()[4:16]
        rv.close()

        rv = client.get("/", headers={"Range": "bytes=4-"})
        assert rv.status_code == 206
        with app.open_resource("static/index.html") as f:
            assert rv.data == f.read()[4:]
        rv.close()

        rv = client.get("/", headers={"Range": "bytes=4-1000"})
        assert rv.status_code == 206
        with app.open_resource("static/index.html") as f:
            assert rv.data == f.read()[4:]
        rv.close()

        rv = client.get("/", headers={"Range": "bytes=-10"})
        assert rv.status_code == 206
        with app.open_resource("static/index.html") as f:
            assert rv.data == f.read()[-10:]
        rv.close()

        rv = client.get("/", headers={"Range": "bytes=1000-"})
        assert rv.status_code == 416
        rv.close()

        rv = client.get("/", headers={"Range": "bytes=-"})
        assert rv.status_code == 416
        rv.close()

        rv = client.get("/", headers={"Range": "somethingsomething"})
        assert rv.status_code == 416
        rv.close()

        last_modified = datetime.datetime.utcfromtimestamp(
            os.path.getmtime(os.path.join(app.root_path, "static/index.html"))
        ).replace(microsecond=0)

        rv = client.get(
            "/", headers={"Range": "bytes=4-15", "If-Range": http_date(last_modified)}
        )
        assert rv.status_code == 206
        rv.close()

        rv = client.get(
            "/",
            headers={
                "Range": "bytes=4-15",
                "If-Range": http_date(datetime.datetime(1999, 1, 1)),
            },
        )
        assert rv.status_code == 200
        rv.close()

    def test_send_file_range_request_bytesio(self, app, client):
        @app.route("/")
        def index():
            file = io.BytesIO(b"somethingsomething")
            return flask.send_file(
                file, attachment_filename="filename", conditional=True
            )

        rv = client.get("/", headers={"Range": "bytes=4-15"})
        assert rv.status_code == 206
        assert rv.data == b"somethingsomething"[4:16]
        rv.close()

    def test_send_file_range_request_xsendfile_invalid(self, app, client):
        # https://github.com/pallets/flask/issues/2526
        app.use_x_sendfile = True

        @app.route("/")
        def index():
            return flask.send_file("static/index.html", conditional=True)

        rv = client.get("/", headers={"Range": "bytes=1000-"})
        assert rv.status_code == 416
        rv.close()

    def test_attachment(self, app, req_ctx):
        app = flask.Flask(__name__)
        with app.test_request_context():
            with open(os.path.join(app.root_path, "static/index.html"), "rb") as f:
                rv = flask.send_file(
                    f, as_attachment=True, attachment_filename="index.html"
                )
                value, options = parse_options_header(rv.headers["Content-Disposition"])
                assert value == "attachment"
                rv.close()

        with open(os.path.join(app.root_path, "static/index.html"), "rb") as f:
            rv = flask.send_file(
                f, as_attachment=True, attachment_filename="index.html"
            )
            value, options = parse_options_header(rv.headers["Content-Disposition"])
            assert value == "attachment"
            assert options["filename"] == "index.html"
            assert "filename*" not in rv.headers["Content-Disposition"]
            rv.close()

        rv = flask.send_file("static/index.html", as_attachment=True)
        value, options = parse_options_header(rv.headers["Content-Disposition"])
        assert value == "attachment"
        assert options["filename"] == "index.html"
        rv.close()

        rv = flask.send_file(
            io.BytesIO(b"Test"),
            as_attachment=True,
            attachment_filename="index.txt",
            add_etags=False,
        )
        assert rv.mimetype == "text/plain"
        value, options = parse_options_header(rv.headers["Content-Disposition"])
        assert value == "attachment"
        assert options["filename"] == "index.txt"
        rv.close()

    @pytest.mark.usefixtures("req_ctx")
    @pytest.mark.parametrize(
        ("filename", "ascii", "utf8"),
        (
            ("index.html", "index.html", False),
            (
                "Ñandú／pingüino.txt",
                '"Nandu/pinguino.txt"',
                "%C3%91and%C3%BA%EF%BC%8Fping%C3%BCino.txt",
            ),
            ("Vögel.txt", "Vogel.txt", "V%C3%B6gel.txt"),
            # ":/" are not safe in filename* value
            ("те:/ст", '":/"', "%D1%82%D0%B5%3A%2F%D1%81%D1%82"),
        ),
    )
    def test_attachment_filename_encoding(self, filename, ascii, utf8):
        rv = flask.send_file(
            "static/index.html", as_attachment=True, attachment_filename=filename
        )
        rv.close()
        content_disposition = rv.headers["Content-Disposition"]
        assert f"filename={ascii}" in content_disposition
        if utf8:
            assert f"filename*=UTF-8''{utf8}" in content_disposition
        else:
            assert "filename*=UTF-8''" not in content_disposition

    def test_static_file(self, app, req_ctx):
        # default cache timeout is 12 hours

        # Test with static file handler.
        rv = app.send_static_file("index.html")
        cc = parse_cache_control_header(rv.headers["Cache-Control"])
        assert cc.max_age == 12 * 60 * 60
        rv.close()
        # Test again with direct use of send_file utility.
        rv = flask.send_file("static/index.html")
        cc = parse_cache_control_header(rv.headers["Cache-Control"])
        assert cc.max_age == 12 * 60 * 60
        rv.close()
        app.config["SEND_FILE_MAX_AGE_DEFAULT"] = 3600

        # Test with static file handler.
        rv = app.send_static_file("index.html")
        cc = parse_cache_control_header(rv.headers["Cache-Control"])
        assert cc.max_age == 3600
        rv.close()
        # Test again with direct use of send_file utility.
        rv = flask.send_file("static/index.html")
        cc = parse_cache_control_header(rv.headers["Cache-Control"])
        assert cc.max_age == 3600
        rv.close()

        # Test with static file handler.
        rv = app.send_static_file(FakePath("index.html"))
        cc = parse_cache_control_header(rv.headers["Cache-Control"])
        assert cc.max_age == 3600
        rv.close()

        class StaticFileApp(flask.Flask):
            def get_send_file_max_age(self, filename):
                return 10

        app = StaticFileApp(__name__)
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file("index.html")
            cc = parse_cache_control_header(rv.headers["Cache-Control"])
            assert cc.max_age == 10
            rv.close()
            # Test again with direct use of send_file utility.
            rv = flask.send_file("static/index.html")
            cc = parse_cache_control_header(rv.headers["Cache-Control"])
            assert cc.max_age == 10
            rv.close()

    def test_send_from_directory(self, app, req_ctx):
        app.root_path = os.path.join(
            os.path.dirname(__file__), "test_apps", "subdomaintestmodule"
        )
        rv = flask.send_from_directory("static", "hello.txt")
        rv.direct_passthrough = False
        assert rv.data.strip() == b"Hello Subdomain"
        rv.close()

    def test_send_from_directory_pathlike(self, app, req_ctx):
        app.root_path = os.path.join(
            os.path.dirname(__file__), "test_apps", "subdomaintestmodule"
        )
        rv = flask.send_from_directory(FakePath("static"), FakePath("hello.txt"))
        rv.direct_passthrough = False
        assert rv.data.strip() == b"Hello Subdomain"
        rv.close()

    def test_send_from_directory_null_character(self, app, req_ctx):
        app.root_path = os.path.join(
            os.path.dirname(__file__), "test_apps", "subdomaintestmodule"
        )

        if sys.version_info >= (3, 8):
            exception = NotFound
        else:
            exception = BadRequest

        with pytest.raises(exception):
            flask.send_from_directory("static", "bad\x00")


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
        @app.route("/")
        def index():
            return "42"

        pytest.raises(ValueError, flask.url_for, "index", _scheme="https")

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


class TestNoImports:
    """Test Flasks are created without import.

    Avoiding ``__import__`` helps create Flask instances where there are errors
    at import time.  Those runtime errors will be apparent to the user soon
    enough, but tools which build Flask instances meta-programmatically benefit
    from a Flask which does not ``__import__``.  Instead of importing to
    retrieve file paths or metadata on a module or package, use the pkgutil and
    imp modules in the Python standard library.
    """

    def test_name_with_import_error(self, modules_tmpdir):
        modules_tmpdir.join("importerror.py").write("raise NotImplementedError()")
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


class TestSafeJoin:
    @pytest.mark.parametrize(
        "args, expected",
        (
            (("a/b/c",), "a/b/c"),
            (("/", "a/", "b/", "c/"), "/a/b/c"),
            (("a", "b", "c"), "a/b/c"),
            (("/a", "b/c"), "/a/b/c"),
            (("a/b", "X/../c"), "a/b/c"),
            (("/a/b", "c/X/.."), "/a/b/c"),
            # If last path is '' add a slash
            (("/a/b/c", ""), "/a/b/c/"),
            # Preserve dot slash
            (("/a/b/c", "./"), "/a/b/c/."),
            (("a/b/c", "X/.."), "a/b/c/."),
            # Base directory is always considered safe
            (("../", "a/b/c"), "../a/b/c"),
            (("/..",), "/.."),
        ),
    )
    def test_safe_join(self, args, expected):
        assert flask.safe_join(*args) == expected

    @pytest.mark.parametrize(
        "args",
        (
            # path.isabs and ``..'' checks
            ("/a", "b", "/c"),
            ("/a", "../b/c"),
            ("/a", "..", "b/c"),
            # Boundaries violations after path normalization
            ("/a", "b/../b/../../c"),
            ("/a", "b", "c/../.."),
            ("/a", "b/../../c"),
        ),
    )
    def test_safe_join_exceptions(self, args):
        with pytest.raises(NotFound):
            print(flask.safe_join(*args))


class TestHelpers:
    @pytest.mark.parametrize(
        "debug, expected_flag, expected_default_flag",
        [
            ("", False, False),
            ("0", False, False),
            ("False", False, False),
            ("No", False, False),
            ("True", True, True),
        ],
    )
    def test_get_debug_flag(
        self, monkeypatch, debug, expected_flag, expected_default_flag
    ):
        monkeypatch.setenv("FLASK_DEBUG", debug)
        if expected_flag is None:
            assert get_debug_flag() is None
        else:
            assert get_debug_flag() == expected_flag
        assert get_debug_flag() == expected_default_flag

    @pytest.mark.parametrize(
        "env, ref_env, debug",
        [
            ("", "production", False),
            ("production", "production", False),
            ("development", "development", True),
            ("other", "other", False),
        ],
    )
    def test_get_env(self, monkeypatch, env, ref_env, debug):
        monkeypatch.setenv("FLASK_ENV", env)
        assert get_debug_flag() == debug
        assert get_env() == ref_env

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
    def test_open_resource(self, mode):
        app = flask.Flask(__name__)

        with app.open_resource("static/index.html", mode) as f:
            assert "<h1>Hello World!</h1>" in str(f.read())

    @pytest.mark.parametrize("mode", ("w", "x", "a", "r+"))
    def test_open_resource_exceptions(self, mode):
        app = flask.Flask(__name__)

        with pytest.raises(ValueError):
            app.open_resource("static/index.html", mode)
