# -*- coding: utf-8 -*-
"""
    tests.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Various helpers.

    :copyright: 2010 Pallets
    :license: BSD-3-Clause
"""
import datetime
import io
import os
import uuid

import pytest
from werkzeug.datastructures import Range
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import NotFound
from werkzeug.http import http_date
from werkzeug.http import parse_cache_control_header
from werkzeug.http import parse_options_header

import flask
from flask import json
from flask._compat import StringIO
from flask._compat import text_type
from flask.helpers import get_debug_flag
from flask.helpers import get_env


def has_encoding(name):
    try:
        import codecs

        codecs.lookup(name)
        return True
    except LookupError:
        return False


class FakePath(object):
    """Fake object to represent a ``PathLike object``.

    This represents a ``pathlib.Path`` object in python 3.
    See: https://www.python.org/dev/peps/pep-0519/
    """

    def __init__(self, path):
        self.path = path

    def __fspath__(self):
        return self.path


class FixedOffset(datetime.tzinfo):
    """Fixed offset in hours east from UTC.

    This is a slight adaptation of the ``FixedOffset`` example found in
    https://docs.python.org/2.7/library/datetime.html.
    """

    def __init__(self, hours, name):
        self.__offset = datetime.timedelta(hours=hours)
        self.__name = name

    def utcoffset(self, dt):
        return self.__offset

    def tzname(self, dt):
        return self.__name

    def dst(self, dt):
        return datetime.timedelta()


class TestJSON(object):
    @pytest.mark.parametrize(
        "value", (1, "t", True, False, None, [], [1, 2, 3], {}, {"foo": u"🐍"})
    )
    @pytest.mark.parametrize(
        "encoding",
        (
            "utf-8",
            "utf-8-sig",
            "utf-16-le",
            "utf-16-be",
            "utf-16",
            "utf-32-le",
            "utf-32-be",
            "utf-32",
        ),
    )
    def test_detect_encoding(self, value, encoding):
        data = json.dumps(value).encode(encoding)
        assert json.detect_encoding(data) == encoding
        assert json.loads(data) == value

    @pytest.mark.parametrize("debug", (True, False))
    def test_bad_request_debug_message(self, app, client, debug):
        app.config["DEBUG"] = debug
        app.config["TRAP_BAD_REQUEST_ERRORS"] = False

        @app.route("/json", methods=["POST"])
        def post_json():
            flask.request.get_json()
            return None

        rv = client.post("/json", data=None, content_type="application/json")
        assert rv.status_code == 400
        contains = b"Failed to decode JSON object" in rv.data
        assert contains == debug

    def test_json_bad_requests(self, app, client):
        @app.route("/json", methods=["POST"])
        def return_json():
            return flask.jsonify(foo=text_type(flask.request.get_json()))

        rv = client.post("/json", data="malformed", content_type="application/json")
        assert rv.status_code == 400

    def test_json_custom_mimetypes(self, app, client):
        @app.route("/json", methods=["POST"])
        def return_json():
            return flask.request.get_json()

        rv = client.post("/json", data='"foo"', content_type="application/x+json")
        assert rv.data == b"foo"

    @pytest.mark.parametrize(
        "test_value,expected", [(True, '"\\u2603"'), (False, u'"\u2603"')]
    )
    def test_json_as_unicode(self, test_value, expected, app, app_ctx):

        app.config["JSON_AS_ASCII"] = test_value
        rv = flask.json.dumps(u"\N{SNOWMAN}")
        assert rv == expected

    def test_json_dump_to_file(self, app, app_ctx):
        test_data = {"name": "Flask"}
        out = StringIO()

        flask.json.dump(test_data, out)
        out.seek(0)
        rv = flask.json.load(out)
        assert rv == test_data

    @pytest.mark.parametrize(
        "test_value", [0, -1, 1, 23, 3.14, "s", "longer string", True, False, None]
    )
    def test_jsonify_basic_types(self, test_value, app, client):
        """Test jsonify with basic types."""

        url = "/jsonify_basic_types"
        app.add_url_rule(url, url, lambda x=test_value: flask.jsonify(x))
        rv = client.get(url)
        assert rv.mimetype == "application/json"
        assert flask.json.loads(rv.data) == test_value

    def test_jsonify_dicts(self, app, client):
        """Test jsonify with dicts and kwargs unpacking."""
        d = {
            "a": 0,
            "b": 23,
            "c": 3.14,
            "d": "t",
            "e": "Hi",
            "f": True,
            "g": False,
            "h": ["test list", 10, False],
            "i": {"test": "dict"},
        }

        @app.route("/kw")
        def return_kwargs():
            return flask.jsonify(**d)

        @app.route("/dict")
        def return_dict():
            return flask.jsonify(d)

        for url in "/kw", "/dict":
            rv = client.get(url)
            assert rv.mimetype == "application/json"
            assert flask.json.loads(rv.data) == d

    def test_jsonify_arrays(self, app, client):
        """Test jsonify of lists and args unpacking."""
        a_list = [
            0,
            42,
            3.14,
            "t",
            "hello",
            True,
            False,
            ["test list", 2, False],
            {"test": "dict"},
        ]

        @app.route("/args_unpack")
        def return_args_unpack():
            return flask.jsonify(*a_list)

        @app.route("/array")
        def return_array():
            return flask.jsonify(a_list)

        for url in "/args_unpack", "/array":
            rv = client.get(url)
            assert rv.mimetype == "application/json"
            assert flask.json.loads(rv.data) == a_list

    def test_jsonify_date_types(self, app, client):
        """Test jsonify with datetime.date and datetime.datetime types."""
        test_dates = (
            datetime.datetime(1973, 3, 11, 6, 30, 45),
            datetime.date(1975, 1, 5),
        )

        for i, d in enumerate(test_dates):
            url = "/datetest{0}".format(i)
            app.add_url_rule(url, str(i), lambda val=d: flask.jsonify(x=val))
            rv = client.get(url)
            assert rv.mimetype == "application/json"
            assert flask.json.loads(rv.data)["x"] == http_date(d.timetuple())

    @pytest.mark.parametrize("tz", (("UTC", 0), ("PST", -8), ("KST", 9)))
    def test_jsonify_aware_datetimes(self, tz):
        """Test if aware datetime.datetime objects are converted into GMT."""
        tzinfo = FixedOffset(hours=tz[1], name=tz[0])
        dt = datetime.datetime(2017, 1, 1, 12, 34, 56, tzinfo=tzinfo)
        gmt = FixedOffset(hours=0, name="GMT")
        expected = dt.astimezone(gmt).strftime('"%a, %d %b %Y %H:%M:%S %Z"')
        assert flask.json.JSONEncoder().encode(dt) == expected

    def test_jsonify_uuid_types(self, app, client):
        """Test jsonify with uuid.UUID types"""

        test_uuid = uuid.UUID(bytes=b"\xDE\xAD\xBE\xEF" * 4)
        url = "/uuid_test"
        app.add_url_rule(url, url, lambda: flask.jsonify(x=test_uuid))

        rv = client.get(url)

        rv_x = flask.json.loads(rv.data)["x"]
        assert rv_x == str(test_uuid)
        rv_uuid = uuid.UUID(rv_x)
        assert rv_uuid == test_uuid

    def test_json_attr(self, app, client):
        @app.route("/add", methods=["POST"])
        def add():
            json = flask.request.get_json()
            return text_type(json["a"] + json["b"])

        rv = client.post(
            "/add",
            data=flask.json.dumps({"a": 1, "b": 2}),
            content_type="application/json",
        )
        assert rv.data == b"3"

    def test_template_escaping(self, app, req_ctx):
        render = flask.render_template_string
        rv = flask.json.htmlsafe_dumps("</script>")
        assert rv == u'"\\u003c/script\\u003e"'
        assert type(rv) == text_type
        rv = render('{{ "</script>"|tojson }}')
        assert rv == '"\\u003c/script\\u003e"'
        rv = render('{{ "<\0/script>"|tojson }}')
        assert rv == '"\\u003c\\u0000/script\\u003e"'
        rv = render('{{ "<!--<script>"|tojson }}')
        assert rv == '"\\u003c!--\\u003cscript\\u003e"'
        rv = render('{{ "&"|tojson }}')
        assert rv == '"\\u0026"'
        rv = render('{{ "\'"|tojson }}')
        assert rv == '"\\u0027"'
        rv = render(
            "<a ng-data='{{ data|tojson }}'></a>", data={"x": ["foo", "bar", "baz'"]}
        )
        assert rv == '<a ng-data=\'{"x": ["foo", "bar", "baz\\u0027"]}\'></a>'

    def test_json_customization(self, app, client):
        class X(object):  # noqa: B903, for Python2 compatibility
            def __init__(self, val):
                self.val = val

        class MyEncoder(flask.json.JSONEncoder):
            def default(self, o):
                if isinstance(o, X):
                    return "<%d>" % o.val
                return flask.json.JSONEncoder.default(self, o)

        class MyDecoder(flask.json.JSONDecoder):
            def __init__(self, *args, **kwargs):
                kwargs.setdefault("object_hook", self.object_hook)
                flask.json.JSONDecoder.__init__(self, *args, **kwargs)

            def object_hook(self, obj):
                if len(obj) == 1 and "_foo" in obj:
                    return X(obj["_foo"])
                return obj

        app.json_encoder = MyEncoder
        app.json_decoder = MyDecoder

        @app.route("/", methods=["POST"])
        def index():
            return flask.json.dumps(flask.request.get_json()["x"])

        rv = client.post(
            "/",
            data=flask.json.dumps({"x": {"_foo": 42}}),
            content_type="application/json",
        )
        assert rv.data == b'"<42>"'

    def test_blueprint_json_customization(self, app, client):
        class X(object):  # noqa: B903, for Python2 compatibility
            def __init__(self, val):
                self.val = val

        class MyEncoder(flask.json.JSONEncoder):
            def default(self, o):
                if isinstance(o, X):
                    return "<%d>" % o.val

                return flask.json.JSONEncoder.default(self, o)

        class MyDecoder(flask.json.JSONDecoder):
            def __init__(self, *args, **kwargs):
                kwargs.setdefault("object_hook", self.object_hook)
                flask.json.JSONDecoder.__init__(self, *args, **kwargs)

            def object_hook(self, obj):
                if len(obj) == 1 and "_foo" in obj:
                    return X(obj["_foo"])

                return obj

        bp = flask.Blueprint("bp", __name__)
        bp.json_encoder = MyEncoder
        bp.json_decoder = MyDecoder

        @bp.route("/bp", methods=["POST"])
        def index():
            return flask.json.dumps(flask.request.get_json()["x"])

        app.register_blueprint(bp)

        rv = client.post(
            "/bp",
            data=flask.json.dumps({"x": {"_foo": 42}}),
            content_type="application/json",
        )
        assert rv.data == b'"<42>"'

    @pytest.mark.skipif(
        not has_encoding("euc-kr"), reason="The euc-kr encoding is required."
    )
    def test_modified_url_encoding(self, app, client):
        class ModifiedRequest(flask.Request):
            url_charset = "euc-kr"

        app.request_class = ModifiedRequest
        app.url_map.charset = "euc-kr"

        @app.route("/")
        def index():
            return flask.request.args["foo"]

        rv = client.get(u"/?foo=정상처리".encode("euc-kr"))
        assert rv.status_code == 200
        assert rv.data == u"정상처리".encode("utf-8")

    def test_json_key_sorting(self, app, client):
        app.debug = True

        assert app.config["JSON_SORT_KEYS"]
        d = dict.fromkeys(range(20), "foo")

        @app.route("/")
        def index():
            return flask.jsonify(values=d)

        rv = client.get("/")
        lines = [x.strip() for x in rv.data.strip().decode("utf-8").splitlines()]
        sorted_by_str = [
            "{",
            '"values": {',
            '"0": "foo",',
            '"1": "foo",',
            '"10": "foo",',
            '"11": "foo",',
            '"12": "foo",',
            '"13": "foo",',
            '"14": "foo",',
            '"15": "foo",',
            '"16": "foo",',
            '"17": "foo",',
            '"18": "foo",',
            '"19": "foo",',
            '"2": "foo",',
            '"3": "foo",',
            '"4": "foo",',
            '"5": "foo",',
            '"6": "foo",',
            '"7": "foo",',
            '"8": "foo",',
            '"9": "foo"',
            "}",
            "}",
        ]
        sorted_by_int = [
            "{",
            '"values": {',
            '"0": "foo",',
            '"1": "foo",',
            '"2": "foo",',
            '"3": "foo",',
            '"4": "foo",',
            '"5": "foo",',
            '"6": "foo",',
            '"7": "foo",',
            '"8": "foo",',
            '"9": "foo",',
            '"10": "foo",',
            '"11": "foo",',
            '"12": "foo",',
            '"13": "foo",',
            '"14": "foo",',
            '"15": "foo",',
            '"16": "foo",',
            '"17": "foo",',
            '"18": "foo",',
            '"19": "foo"',
            "}",
            "}",
        ]

        try:
            assert lines == sorted_by_int
        except AssertionError:
            assert lines == sorted_by_str


class TestSendfile(object):
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
                StringIO("party like it's"),
                last_modified=last_modified,
                mimetype="text/plain",
            )

        rv = client.get("/")
        assert rv.last_modified == last_modified

    def test_send_file_object_without_mimetype(self, app, req_ctx):
        with pytest.raises(ValueError) as excinfo:
            flask.send_file(StringIO("LOL"))
        assert "Unable to infer MIME-type" in str(excinfo.value)
        assert "no filename is available" in str(excinfo.value)

        flask.send_file(StringIO("LOL"), attachment_filename="filename")

    def test_send_file_object(self, app, req_ctx):
        with open(os.path.join(app.root_path, "static/index.html"), mode="rb") as f:
            rv = flask.send_file(f, mimetype="text/html")
            rv.direct_passthrough = False
            with app.open_resource("static/index.html") as f:
                assert rv.data == f.read()
            assert rv.mimetype == "text/html"
            rv.close()

        app.use_x_sendfile = True

        with open(os.path.join(app.root_path, "static/index.html")) as f:
            rv = flask.send_file(f, mimetype="text/html")
            assert rv.mimetype == "text/html"
            assert "x-sendfile" not in rv.headers
            rv.close()

        app.use_x_sendfile = False
        f = StringIO("Test")
        rv = flask.send_file(f, mimetype="application/octet-stream")
        rv.direct_passthrough = False
        assert rv.data == b"Test"
        assert rv.mimetype == "application/octet-stream"
        rv.close()

        class PyStringIO(object):
            def __init__(self, *args, **kwargs):
                self._io = StringIO(*args, **kwargs)

            def __getattr__(self, name):
                return getattr(self._io, name)

        f = PyStringIO("Test")
        f.name = "test.txt"
        rv = flask.send_file(f, attachment_filename=f.name)
        rv.direct_passthrough = False
        assert rv.data == b"Test"
        assert rv.mimetype == "text/plain"
        rv.close()

        f = StringIO("Test")
        rv = flask.send_file(f, mimetype="text/plain")
        rv.direct_passthrough = False
        assert rv.data == b"Test"
        assert rv.mimetype == "text/plain"
        rv.close()

        app.use_x_sendfile = True

        f = StringIO("Test")
        rv = flask.send_file(f, mimetype="text/html")
        assert "x-sendfile" not in rv.headers
        rv.close()

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

    @pytest.mark.skipif(
        not callable(getattr(Range, "to_content_range_header", None)),
        reason="not implemented within werkzeug",
    )
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
            with open(os.path.join(app.root_path, "static/index.html")) as f:
                rv = flask.send_file(
                    f, as_attachment=True, attachment_filename="index.html"
                )
                value, options = parse_options_header(rv.headers["Content-Disposition"])
                assert value == "attachment"
                rv.close()

        with open(os.path.join(app.root_path, "static/index.html")) as f:
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
            StringIO("Test"),
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
                u"Ñandú／pingüino.txt",
                '"Nandu/pinguino.txt"',
                "%C3%91and%C3%BA%EF%BC%8Fping%C3%BCino.txt",
            ),
            (u"Vögel.txt", "Vogel.txt", "V%C3%B6gel.txt"),
            # Native string not marked as Unicode on Python 2
            ("tést.txt", "test.txt", "t%C3%A9st.txt"),
            # ":/" are not safe in filename* value
            (u"те:/ст", '":/"', "%D1%82%D0%B5%3A%2F%D1%81%D1%82"),
        ),
    )
    def test_attachment_filename_encoding(self, filename, ascii, utf8):
        rv = flask.send_file(
            "static/index.html", as_attachment=True, attachment_filename=filename
        )
        rv.close()
        content_disposition = rv.headers["Content-Disposition"]
        assert "filename=%s" % ascii in content_disposition
        if utf8:
            assert "filename*=UTF-8''" + utf8 in content_disposition
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

    def test_send_from_directory_bad_request(self, app, req_ctx):
        app.root_path = os.path.join(
            os.path.dirname(__file__), "test_apps", "subdomaintestmodule"
        )

        with pytest.raises(BadRequest):
            flask.send_from_directory("static", "bad\x00")


class TestUrlFor(object):
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
                return "Get %d" % id

            def post(self):
                return "Create"

        myview = MyView.as_view("myview")
        app.add_url_rule("/myview/", methods=["GET"], view_func=myview)
        app.add_url_rule("/myview/<int:id>", methods=["GET"], view_func=myview)
        app.add_url_rule("/myview/create", methods=["POST"], view_func=myview)

        assert flask.url_for("myview", _method="GET") == "/myview/"
        assert flask.url_for("myview", id=42, _method="GET") == "/myview/42"
        assert flask.url_for("myview", _method="POST") == "/myview/create"


class TestNoImports(object):
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


class TestStreaming(object):
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

        class Wrapper(object):
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


class TestSafeJoin(object):
    def test_safe_join(self):
        # Valid combinations of *args and expected joined paths.
        passing = (
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
        )

        for args, expected in passing:
            assert flask.safe_join(*args) == expected

    def test_safe_join_exceptions(self):
        # Should raise werkzeug.exceptions.NotFound on unsafe joins.
        failing = (
            # path.isabs and ``..'' checks
            ("/a", "b", "/c"),
            ("/a", "../b/c"),
            ("/a", "..", "b/c"),
            # Boundaries violations after path normalization
            ("/a", "b/../b/../../c"),
            ("/a", "b", "c/../.."),
            ("/a", "b/../../c"),
        )

        for args in failing:
            with pytest.raises(NotFound):
                print(flask.safe_join(*args))


class TestHelpers(object):
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
