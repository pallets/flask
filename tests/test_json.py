import datetime
import decimal
import io
import uuid

import pytest
from werkzeug.http import http_date

import flask
from flask import json


@pytest.mark.parametrize("debug", (True, False))
def test_bad_request_debug_message(app, client, debug):
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


def test_json_bad_requests(app, client):
    @app.route("/json", methods=["POST"])
    def return_json():
        return flask.jsonify(foo=str(flask.request.get_json()))

    rv = client.post("/json", data="malformed", content_type="application/json")
    assert rv.status_code == 400


def test_json_custom_mimetypes(app, client):
    @app.route("/json", methods=["POST"])
    def return_json():
        return flask.request.get_json()

    rv = client.post("/json", data='"foo"', content_type="application/x+json")
    assert rv.data == b"foo"


@pytest.mark.parametrize(
    "test_value,expected", [(True, '"\\u2603"'), (False, '"\u2603"')]
)
def test_json_as_unicode(test_value, expected, app, app_ctx):

    app.config["JSON_AS_ASCII"] = test_value
    rv = flask.json.dumps("\N{SNOWMAN}")
    assert rv == expected


def test_json_dump_to_file(app, app_ctx):
    test_data = {"name": "Flask"}
    out = io.StringIO()

    flask.json.dump(test_data, out)
    out.seek(0)
    rv = flask.json.load(out)
    assert rv == test_data


@pytest.mark.parametrize(
    "test_value", [0, -1, 1, 23, 3.14, "s", "longer string", True, False, None]
)
def test_jsonify_basic_types(test_value, app, client):
    url = "/jsonify_basic_types"
    app.add_url_rule(url, url, lambda x=test_value: flask.jsonify(x))
    rv = client.get(url)
    assert rv.mimetype == "application/json"
    assert flask.json.loads(rv.data) == test_value


def test_jsonify_dicts(app, client):
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


def test_jsonify_arrays(app, client):
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


@pytest.mark.parametrize(
    "value", [datetime.datetime(1973, 3, 11, 6, 30, 45), datetime.date(1975, 1, 5)]
)
def test_jsonify_datetime(app, client, value):
    @app.route("/")
    def index():
        return flask.jsonify(value=value)

    r = client.get()
    assert r.json["value"] == http_date(value)


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


@pytest.mark.parametrize("tz", (("UTC", 0), ("PST", -8), ("KST", 9)))
def test_jsonify_aware_datetimes(tz):
    """Test if aware datetime.datetime objects are converted into GMT."""
    tzinfo = FixedOffset(hours=tz[1], name=tz[0])
    dt = datetime.datetime(2017, 1, 1, 12, 34, 56, tzinfo=tzinfo)
    gmt = FixedOffset(hours=0, name="GMT")
    expected = dt.astimezone(gmt).strftime('"%a, %d %b %Y %H:%M:%S %Z"')
    assert flask.json.JSONEncoder().encode(dt) == expected


def test_jsonify_uuid_types(app, client):
    """Test jsonify with uuid.UUID types"""

    test_uuid = uuid.UUID(bytes=b"\xDE\xAD\xBE\xEF" * 4)
    url = "/uuid_test"
    app.add_url_rule(url, url, lambda: flask.jsonify(x=test_uuid))

    rv = client.get(url)

    rv_x = flask.json.loads(rv.data)["x"]
    assert rv_x == str(test_uuid)
    rv_uuid = uuid.UUID(rv_x)
    assert rv_uuid == test_uuid


def test_json_decimal():
    rv = flask.json.dumps(decimal.Decimal("0.003"))
    assert rv == '"0.003"'


def test_json_attr(app, client):
    @app.route("/add", methods=["POST"])
    def add():
        json = flask.request.get_json()
        return str(json["a"] + json["b"])

    rv = client.post(
        "/add",
        data=flask.json.dumps({"a": 1, "b": 2}),
        content_type="application/json",
    )
    assert rv.data == b"3"


def test_tojson_filter(app, req_ctx):
    # The tojson filter is tested in Jinja, this confirms that it's
    # using Flask's dumps.
    rv = flask.render_template_string(
        "const data = {{ data|tojson }};",
        data={"name": "</script>", "time": datetime.datetime(2021, 2, 1, 7, 15)},
    )
    assert rv == (
        'const data = {"name": "\\u003c/script\\u003e",'
        ' "time": "Mon, 01 Feb 2021 07:15:00 GMT"};'
    )


def test_json_customization(app, client):
    class X:  # noqa: B903, for Python2 compatibility
        def __init__(self, val):
            self.val = val

    class MyEncoder(flask.json.JSONEncoder):
        def default(self, o):
            if isinstance(o, X):
                return f"<{o.val}>"
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


def test_blueprint_json_customization(app, client):
    class X:
        __slots__ = ("val",)

        def __init__(self, val):
            self.val = val

    class MyEncoder(flask.json.JSONEncoder):
        def default(self, o):
            if isinstance(o, X):
                return f"<{o.val}>"

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


def _has_encoding(name):
    try:
        import codecs

        codecs.lookup(name)
        return True
    except LookupError:
        return False


@pytest.mark.skipif(
    not _has_encoding("euc-kr"), reason="The euc-kr encoding is required."
)
def test_modified_url_encoding(app, client):
    class ModifiedRequest(flask.Request):
        url_charset = "euc-kr"

    app.request_class = ModifiedRequest
    app.url_map.charset = "euc-kr"

    @app.route("/")
    def index():
        return flask.request.args["foo"]

    rv = client.get("/", query_string={"foo": "정상처리"}, charset="euc-kr")
    assert rv.status_code == 200
    assert rv.get_data(as_text=True) == "정상처리"


def test_json_key_sorting(app, client):
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


def test_html_method():
    class ObjectWithHTML:
        def __html__(self):
            return "<p>test</p>"

    result = json.dumps(ObjectWithHTML())
    assert result == '"<p>test</p>"'
