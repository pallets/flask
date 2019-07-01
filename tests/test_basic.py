# -*- coding: utf-8 -*-
"""
    tests.basic
    ~~~~~~~~~~~~~~~~~~~~~

    The basic functionality.

    :copyright: 2010 Pallets
    :license: BSD-3-Clause
"""
import re
import sys
import time
import uuid
from datetime import datetime
from threading import Thread

import pytest
import werkzeug.serving
from werkzeug.exceptions import BadRequest
from werkzeug.exceptions import Forbidden
from werkzeug.exceptions import NotFound
from werkzeug.http import parse_date
from werkzeug.routing import BuildError

import flask
from flask._compat import text_type


def test_options_work(app, client):
    @app.route("/", methods=["GET", "POST"])
    def index():
        return "Hello World"

    rv = client.open("/", method="OPTIONS")
    assert sorted(rv.allow) == ["GET", "HEAD", "OPTIONS", "POST"]
    assert rv.data == b""


def test_options_on_multiple_rules(app, client):
    @app.route("/", methods=["GET", "POST"])
    def index():
        return "Hello World"

    @app.route("/", methods=["PUT"])
    def index_put():
        return "Aha!"

    rv = client.open("/", method="OPTIONS")
    assert sorted(rv.allow) == ["GET", "HEAD", "OPTIONS", "POST", "PUT"]


def test_provide_automatic_options_attr():
    app = flask.Flask(__name__)

    def index():
        return "Hello World!"

    index.provide_automatic_options = False
    app.route("/")(index)
    rv = app.test_client().open("/", method="OPTIONS")
    assert rv.status_code == 405

    app = flask.Flask(__name__)

    def index2():
        return "Hello World!"

    index2.provide_automatic_options = True
    app.route("/", methods=["OPTIONS"])(index2)
    rv = app.test_client().open("/", method="OPTIONS")
    assert sorted(rv.allow) == ["OPTIONS"]


def test_provide_automatic_options_kwarg(app, client):
    def index():
        return flask.request.method

    def more():
        return flask.request.method

    app.add_url_rule("/", view_func=index, provide_automatic_options=False)
    app.add_url_rule(
        "/more",
        view_func=more,
        methods=["GET", "POST"],
        provide_automatic_options=False,
    )
    assert client.get("/").data == b"GET"

    rv = client.post("/")
    assert rv.status_code == 405
    assert sorted(rv.allow) == ["GET", "HEAD"]

    # Older versions of Werkzeug.test.Client don't have an options method
    if hasattr(client, "options"):
        rv = client.options("/")
    else:
        rv = client.open("/", method="OPTIONS")

    assert rv.status_code == 405

    rv = client.head("/")
    assert rv.status_code == 200
    assert not rv.data  # head truncates
    assert client.post("/more").data == b"POST"
    assert client.get("/more").data == b"GET"

    rv = client.delete("/more")
    assert rv.status_code == 405
    assert sorted(rv.allow) == ["GET", "HEAD", "POST"]

    if hasattr(client, "options"):
        rv = client.options("/more")
    else:
        rv = client.open("/more", method="OPTIONS")

    assert rv.status_code == 405


def test_request_dispatching(app, client):
    @app.route("/")
    def index():
        return flask.request.method

    @app.route("/more", methods=["GET", "POST"])
    def more():
        return flask.request.method

    assert client.get("/").data == b"GET"
    rv = client.post("/")
    assert rv.status_code == 405
    assert sorted(rv.allow) == ["GET", "HEAD", "OPTIONS"]
    rv = client.head("/")
    assert rv.status_code == 200
    assert not rv.data  # head truncates
    assert client.post("/more").data == b"POST"
    assert client.get("/more").data == b"GET"
    rv = client.delete("/more")
    assert rv.status_code == 405
    assert sorted(rv.allow) == ["GET", "HEAD", "OPTIONS", "POST"]


def test_disallow_string_for_allowed_methods(app):
    with pytest.raises(TypeError):

        @app.route("/", methods="GET POST")
        def index():
            return "Hey"


def test_url_mapping(app, client):
    random_uuid4 = "7eb41166-9ebf-4d26-b771-ea3f54f8b383"

    def index():
        return flask.request.method

    def more():
        return flask.request.method

    def options():
        return random_uuid4

    app.add_url_rule("/", "index", index)
    app.add_url_rule("/more", "more", more, methods=["GET", "POST"])

    # Issue 1288: Test that automatic options are not added
    #             when non-uppercase 'options' in methods
    app.add_url_rule("/options", "options", options, methods=["options"])

    assert client.get("/").data == b"GET"
    rv = client.post("/")
    assert rv.status_code == 405
    assert sorted(rv.allow) == ["GET", "HEAD", "OPTIONS"]
    rv = client.head("/")
    assert rv.status_code == 200
    assert not rv.data  # head truncates
    assert client.post("/more").data == b"POST"
    assert client.get("/more").data == b"GET"
    rv = client.delete("/more")
    assert rv.status_code == 405
    assert sorted(rv.allow) == ["GET", "HEAD", "OPTIONS", "POST"]
    rv = client.open("/options", method="OPTIONS")
    assert rv.status_code == 200
    assert random_uuid4 in rv.data.decode("utf-8")


def test_werkzeug_routing(app, client):
    from werkzeug.routing import Submount, Rule

    app.url_map.add(
        Submount("/foo", [Rule("/bar", endpoint="bar"), Rule("/", endpoint="index")])
    )

    def bar():
        return "bar"

    def index():
        return "index"

    app.view_functions["bar"] = bar
    app.view_functions["index"] = index

    assert client.get("/foo/").data == b"index"
    assert client.get("/foo/bar").data == b"bar"


def test_endpoint_decorator(app, client):
    from werkzeug.routing import Submount, Rule

    app.url_map.add(
        Submount("/foo", [Rule("/bar", endpoint="bar"), Rule("/", endpoint="index")])
    )

    @app.endpoint("bar")
    def bar():
        return "bar"

    @app.endpoint("index")
    def index():
        return "index"

    assert client.get("/foo/").data == b"index"
    assert client.get("/foo/bar").data == b"bar"


def test_session(app, client):
    @app.route("/set", methods=["POST"])
    def set():
        assert not flask.session.accessed
        assert not flask.session.modified
        flask.session["value"] = flask.request.form["value"]
        assert flask.session.accessed
        assert flask.session.modified
        return "value set"

    @app.route("/get")
    def get():
        assert not flask.session.accessed
        assert not flask.session.modified
        v = flask.session.get("value", "None")
        assert flask.session.accessed
        assert not flask.session.modified
        return v

    assert client.post("/set", data={"value": "42"}).data == b"value set"
    assert client.get("/get").data == b"42"


def test_session_using_server_name(app, client):
    app.config.update(SERVER_NAME="example.com")

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "Hello World"

    rv = client.get("/", "http://example.com/")
    assert "domain=.example.com" in rv.headers["set-cookie"].lower()
    assert "httponly" in rv.headers["set-cookie"].lower()


def test_session_using_server_name_and_port(app, client):
    app.config.update(SERVER_NAME="example.com:8080")

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "Hello World"

    rv = client.get("/", "http://example.com:8080/")
    assert "domain=.example.com" in rv.headers["set-cookie"].lower()
    assert "httponly" in rv.headers["set-cookie"].lower()


def test_session_using_server_name_port_and_path(app, client):
    app.config.update(SERVER_NAME="example.com:8080", APPLICATION_ROOT="/foo")

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "Hello World"

    rv = client.get("/", "http://example.com:8080/foo")
    assert "domain=example.com" in rv.headers["set-cookie"].lower()
    assert "path=/foo" in rv.headers["set-cookie"].lower()
    assert "httponly" in rv.headers["set-cookie"].lower()


def test_session_using_application_root(app, client):
    class PrefixPathMiddleware(object):
        def __init__(self, app, prefix):
            self.app = app
            self.prefix = prefix

        def __call__(self, environ, start_response):
            environ["SCRIPT_NAME"] = self.prefix
            return self.app(environ, start_response)

    app.wsgi_app = PrefixPathMiddleware(app.wsgi_app, "/bar")
    app.config.update(APPLICATION_ROOT="/bar")

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "Hello World"

    rv = client.get("/", "http://example.com:8080/")
    assert "path=/bar" in rv.headers["set-cookie"].lower()


def test_session_using_session_settings(app, client):
    app.config.update(
        SERVER_NAME="www.example.com:8080",
        APPLICATION_ROOT="/test",
        SESSION_COOKIE_DOMAIN=".example.com",
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_SAMESITE="Lax",
        SESSION_COOKIE_PATH="/",
    )

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "Hello World"

    rv = client.get("/", "http://www.example.com:8080/test/")
    cookie = rv.headers["set-cookie"].lower()
    assert "domain=.example.com" in cookie
    assert "path=/" in cookie
    assert "secure" in cookie
    assert "httponly" not in cookie
    assert "samesite" in cookie


def test_session_using_samesite_attribute(app, client):
    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "Hello World"

    app.config.update(SESSION_COOKIE_SAMESITE="invalid")

    with pytest.raises(ValueError):
        client.get("/")

    app.config.update(SESSION_COOKIE_SAMESITE=None)
    rv = client.get("/")
    cookie = rv.headers["set-cookie"].lower()
    assert "samesite" not in cookie

    app.config.update(SESSION_COOKIE_SAMESITE="Strict")
    rv = client.get("/")
    cookie = rv.headers["set-cookie"].lower()
    assert "samesite=strict" in cookie

    app.config.update(SESSION_COOKIE_SAMESITE="Lax")
    rv = client.get("/")
    cookie = rv.headers["set-cookie"].lower()
    assert "samesite=lax" in cookie


def test_session_localhost_warning(recwarn, app, client):
    app.config.update(SERVER_NAME="localhost:5000")

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "testing"

    rv = client.get("/", "http://localhost:5000/")
    assert "domain" not in rv.headers["set-cookie"].lower()
    w = recwarn.pop(UserWarning)
    assert '"localhost" is not a valid cookie domain' in str(w.message)


def test_session_ip_warning(recwarn, app, client):
    app.config.update(SERVER_NAME="127.0.0.1:5000")

    @app.route("/")
    def index():
        flask.session["testing"] = 42
        return "testing"

    rv = client.get("/", "http://127.0.0.1:5000/")
    assert "domain=127.0.0.1" in rv.headers["set-cookie"].lower()
    w = recwarn.pop(UserWarning)
    assert "cookie domain is an IP" in str(w.message)


def test_missing_session(app):
    app.secret_key = None

    def expect_exception(f, *args, **kwargs):
        e = pytest.raises(RuntimeError, f, *args, **kwargs)
        assert e.value.args and "session is unavailable" in e.value.args[0]

    with app.test_request_context():
        assert flask.session.get("missing_key") is None
        expect_exception(flask.session.__setitem__, "foo", 42)
        expect_exception(flask.session.pop, "foo")


def test_session_expiration(app, client):
    permanent = True

    @app.route("/")
    def index():
        flask.session["test"] = 42
        flask.session.permanent = permanent
        return ""

    @app.route("/test")
    def test():
        return text_type(flask.session.permanent)

    rv = client.get("/")
    assert "set-cookie" in rv.headers
    match = re.search(r"(?i)\bexpires=([^;]+)", rv.headers["set-cookie"])
    expires = parse_date(match.group())
    expected = datetime.utcnow() + app.permanent_session_lifetime
    assert expires.year == expected.year
    assert expires.month == expected.month
    assert expires.day == expected.day

    rv = client.get("/test")
    assert rv.data == b"True"

    permanent = False
    rv = client.get("/")
    assert "set-cookie" in rv.headers
    match = re.search(r"\bexpires=([^;]+)", rv.headers["set-cookie"])
    assert match is None


def test_session_stored_last(app, client):
    @app.after_request
    def modify_session(response):
        flask.session["foo"] = 42
        return response

    @app.route("/")
    def dump_session_contents():
        return repr(flask.session.get("foo"))

    assert client.get("/").data == b"None"
    assert client.get("/").data == b"42"


def test_session_special_types(app, client):
    now = datetime.utcnow().replace(microsecond=0)
    the_uuid = uuid.uuid4()

    @app.route("/")
    def dump_session_contents():
        flask.session["t"] = (1, 2, 3)
        flask.session["b"] = b"\xff"
        flask.session["m"] = flask.Markup("<html>")
        flask.session["u"] = the_uuid
        flask.session["d"] = now
        flask.session["t_tag"] = {" t": "not-a-tuple"}
        flask.session["di_t_tag"] = {" t__": "not-a-tuple"}
        flask.session["di_tag"] = {" di": "not-a-dict"}
        return "", 204

    with client:
        client.get("/")
        s = flask.session
        assert s["t"] == (1, 2, 3)
        assert type(s["b"]) == bytes
        assert s["b"] == b"\xff"
        assert type(s["m"]) == flask.Markup
        assert s["m"] == flask.Markup("<html>")
        assert s["u"] == the_uuid
        assert s["d"] == now
        assert s["t_tag"] == {" t": "not-a-tuple"}
        assert s["di_t_tag"] == {" t__": "not-a-tuple"}
        assert s["di_tag"] == {" di": "not-a-dict"}


def test_session_cookie_setting(app):
    is_permanent = True

    @app.route("/bump")
    def bump():
        rv = flask.session["foo"] = flask.session.get("foo", 0) + 1
        flask.session.permanent = is_permanent
        return str(rv)

    @app.route("/read")
    def read():
        return str(flask.session.get("foo", 0))

    def run_test(expect_header):
        with app.test_client() as c:
            assert c.get("/bump").data == b"1"
            assert c.get("/bump").data == b"2"
            assert c.get("/bump").data == b"3"

            rv = c.get("/read")
            set_cookie = rv.headers.get("set-cookie")
            assert (set_cookie is not None) == expect_header
            assert rv.data == b"3"

    is_permanent = True
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True
    run_test(expect_header=True)

    is_permanent = True
    app.config["SESSION_REFRESH_EACH_REQUEST"] = False
    run_test(expect_header=False)

    is_permanent = False
    app.config["SESSION_REFRESH_EACH_REQUEST"] = True
    run_test(expect_header=False)

    is_permanent = False
    app.config["SESSION_REFRESH_EACH_REQUEST"] = False
    run_test(expect_header=False)


def test_session_vary_cookie(app, client):
    @app.route("/set")
    def set_session():
        flask.session["test"] = "test"
        return ""

    @app.route("/get")
    def get():
        return flask.session.get("test")

    @app.route("/getitem")
    def getitem():
        return flask.session["test"]

    @app.route("/setdefault")
    def setdefault():
        return flask.session.setdefault("test", "default")

    @app.route("/vary-cookie-header-set")
    def vary_cookie_header_set():
        response = flask.Response()
        response.vary.add("Cookie")
        flask.session["test"] = "test"
        return response

    @app.route("/vary-header-set")
    def vary_header_set():
        response = flask.Response()
        response.vary.update(("Accept-Encoding", "Accept-Language"))
        flask.session["test"] = "test"
        return response

    @app.route("/no-vary-header")
    def no_vary_header():
        return ""

    def expect(path, header_value="Cookie"):
        rv = client.get(path)

        if header_value:
            # The 'Vary' key should exist in the headers only once.
            assert len(rv.headers.get_all("Vary")) == 1
            assert rv.headers["Vary"] == header_value
        else:
            assert "Vary" not in rv.headers

    expect("/set")
    expect("/get")
    expect("/getitem")
    expect("/setdefault")
    expect("/vary-cookie-header-set")
    expect("/vary-header-set", "Accept-Encoding, Accept-Language, Cookie")
    expect("/no-vary-header", None)


def test_flashes(app, req_ctx):
    assert not flask.session.modified
    flask.flash("Zap")
    flask.session.modified = False
    flask.flash("Zip")
    assert flask.session.modified
    assert list(flask.get_flashed_messages()) == ["Zap", "Zip"]


def test_extended_flashing(app):
    # Be sure app.testing=True below, else tests can fail silently.
    #
    # Specifically, if app.testing is not set to True, the AssertionErrors
    # in the view functions will cause a 500 response to the test client
    # instead of propagating exceptions.

    @app.route("/")
    def index():
        flask.flash(u"Hello World")
        flask.flash(u"Hello World", "error")
        flask.flash(flask.Markup(u"<em>Testing</em>"), "warning")
        return ""

    @app.route("/test/")
    def test():
        messages = flask.get_flashed_messages()
        assert list(messages) == [
            u"Hello World",
            u"Hello World",
            flask.Markup(u"<em>Testing</em>"),
        ]
        return ""

    @app.route("/test_with_categories/")
    def test_with_categories():
        messages = flask.get_flashed_messages(with_categories=True)
        assert len(messages) == 3
        assert list(messages) == [
            ("message", u"Hello World"),
            ("error", u"Hello World"),
            ("warning", flask.Markup(u"<em>Testing</em>")),
        ]
        return ""

    @app.route("/test_filter/")
    def test_filter():
        messages = flask.get_flashed_messages(
            category_filter=["message"], with_categories=True
        )
        assert list(messages) == [("message", u"Hello World")]
        return ""

    @app.route("/test_filters/")
    def test_filters():
        messages = flask.get_flashed_messages(
            category_filter=["message", "warning"], with_categories=True
        )
        assert list(messages) == [
            ("message", u"Hello World"),
            ("warning", flask.Markup(u"<em>Testing</em>")),
        ]
        return ""

    @app.route("/test_filters_without_returning_categories/")
    def test_filters2():
        messages = flask.get_flashed_messages(category_filter=["message", "warning"])
        assert len(messages) == 2
        assert messages[0] == u"Hello World"
        assert messages[1] == flask.Markup(u"<em>Testing</em>")
        return ""

    # Create new test client on each test to clean flashed messages.

    client = app.test_client()
    client.get("/")
    client.get("/test_with_categories/")

    client = app.test_client()
    client.get("/")
    client.get("/test_filter/")

    client = app.test_client()
    client.get("/")
    client.get("/test_filters/")

    client = app.test_client()
    client.get("/")
    client.get("/test_filters_without_returning_categories/")


def test_request_processing(app, client):
    evts = []

    @app.before_request
    def before_request():
        evts.append("before")

    @app.after_request
    def after_request(response):
        response.data += b"|after"
        evts.append("after")
        return response

    @app.route("/")
    def index():
        assert "before" in evts
        assert "after" not in evts
        return "request"

    assert "after" not in evts
    rv = client.get("/").data
    assert "after" in evts
    assert rv == b"request|after"


def test_request_preprocessing_early_return(app, client):
    evts = []

    @app.before_request
    def before_request1():
        evts.append(1)

    @app.before_request
    def before_request2():
        evts.append(2)
        return "hello"

    @app.before_request
    def before_request3():
        evts.append(3)
        return "bye"

    @app.route("/")
    def index():
        evts.append("index")
        return "damnit"

    rv = client.get("/").data.strip()
    assert rv == b"hello"
    assert evts == [1, 2]


def test_after_request_processing(app, client):
    @app.route("/")
    def index():
        @flask.after_this_request
        def foo(response):
            response.headers["X-Foo"] = "a header"
            return response

        return "Test"

    resp = client.get("/")
    assert resp.status_code == 200
    assert resp.headers["X-Foo"] == "a header"


def test_teardown_request_handler(app, client):
    called = []

    @app.teardown_request
    def teardown_request(exc):
        called.append(True)
        return "Ignored"

    @app.route("/")
    def root():
        return "Response"

    rv = client.get("/")
    assert rv.status_code == 200
    assert b"Response" in rv.data
    assert len(called) == 1


def test_teardown_request_handler_debug_mode(app, client):
    called = []

    @app.teardown_request
    def teardown_request(exc):
        called.append(True)
        return "Ignored"

    @app.route("/")
    def root():
        return "Response"

    rv = client.get("/")
    assert rv.status_code == 200
    assert b"Response" in rv.data
    assert len(called) == 1


def test_teardown_request_handler_error(app, client):
    called = []
    app.testing = False

    @app.teardown_request
    def teardown_request1(exc):
        assert type(exc) == ZeroDivisionError
        called.append(True)
        # This raises a new error and blows away sys.exc_info(), so we can
        # test that all teardown_requests get passed the same original
        # exception.
        try:
            raise TypeError()
        except Exception:
            pass

    @app.teardown_request
    def teardown_request2(exc):
        assert type(exc) == ZeroDivisionError
        called.append(True)
        # This raises a new error and blows away sys.exc_info(), so we can
        # test that all teardown_requests get passed the same original
        # exception.
        try:
            raise TypeError()
        except Exception:
            pass

    @app.route("/")
    def fails():
        1 // 0

    rv = client.get("/")
    assert rv.status_code == 500
    assert b"Internal Server Error" in rv.data
    assert len(called) == 2


def test_before_after_request_order(app, client):
    called = []

    @app.before_request
    def before1():
        called.append(1)

    @app.before_request
    def before2():
        called.append(2)

    @app.after_request
    def after1(response):
        called.append(4)
        return response

    @app.after_request
    def after2(response):
        called.append(3)
        return response

    @app.teardown_request
    def finish1(exc):
        called.append(6)

    @app.teardown_request
    def finish2(exc):
        called.append(5)

    @app.route("/")
    def index():
        return "42"

    rv = client.get("/")
    assert rv.data == b"42"
    assert called == [1, 2, 3, 4, 5, 6]


def test_error_handling(app, client):
    app.testing = False

    @app.errorhandler(404)
    def not_found(e):
        return "not found", 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return "internal server error", 500

    @app.errorhandler(Forbidden)
    def forbidden(e):
        return "forbidden", 403

    @app.route("/")
    def index():
        flask.abort(404)

    @app.route("/error")
    def error():
        1 // 0

    @app.route("/forbidden")
    def error2():
        flask.abort(403)

    rv = client.get("/")
    assert rv.status_code == 404
    assert rv.data == b"not found"
    rv = client.get("/error")
    assert rv.status_code == 500
    assert b"internal server error" == rv.data
    rv = client.get("/forbidden")
    assert rv.status_code == 403
    assert b"forbidden" == rv.data


def test_error_handler_unknown_code(app):
    with pytest.raises(KeyError) as exc_info:
        app.register_error_handler(999, lambda e: ("999", 999))

    assert "Use a subclass" in exc_info.value.args[0]


def test_error_handling_processing(app, client):
    app.testing = False

    @app.errorhandler(500)
    def internal_server_error(e):
        return "internal server error", 500

    @app.route("/")
    def broken_func():
        1 // 0

    @app.after_request
    def after_request(resp):
        resp.mimetype = "text/x-special"
        return resp

    resp = client.get("/")
    assert resp.mimetype == "text/x-special"
    assert resp.data == b"internal server error"


def test_baseexception_error_handling(app, client):
    app.testing = False

    @app.route("/")
    def broken_func():
        raise KeyboardInterrupt()

    with pytest.raises(KeyboardInterrupt):
        client.get("/")

        ctx = flask._request_ctx_stack.top
        assert ctx.preserved
        assert type(ctx._preserved_exc) is KeyboardInterrupt


def test_before_request_and_routing_errors(app, client):
    @app.before_request
    def attach_something():
        flask.g.something = "value"

    @app.errorhandler(404)
    def return_something(error):
        return flask.g.something, 404

    rv = client.get("/")
    assert rv.status_code == 404
    assert rv.data == b"value"


def test_user_error_handling(app, client):
    class MyException(Exception):
        pass

    @app.errorhandler(MyException)
    def handle_my_exception(e):
        assert isinstance(e, MyException)
        return "42"

    @app.route("/")
    def index():
        raise MyException()

    assert client.get("/").data == b"42"


def test_http_error_subclass_handling(app, client):
    class ForbiddenSubclass(Forbidden):
        pass

    @app.errorhandler(ForbiddenSubclass)
    def handle_forbidden_subclass(e):
        assert isinstance(e, ForbiddenSubclass)
        return "banana"

    @app.errorhandler(403)
    def handle_403(e):
        assert not isinstance(e, ForbiddenSubclass)
        assert isinstance(e, Forbidden)
        return "apple"

    @app.route("/1")
    def index1():
        raise ForbiddenSubclass()

    @app.route("/2")
    def index2():
        flask.abort(403)

    @app.route("/3")
    def index3():
        raise Forbidden()

    assert client.get("/1").data == b"banana"
    assert client.get("/2").data == b"apple"
    assert client.get("/3").data == b"apple"


def test_errorhandler_precedence(app, client):
    class E1(Exception):
        pass

    class E2(Exception):
        pass

    class E3(E1, E2):
        pass

    @app.errorhandler(E2)
    def handle_e2(e):
        return "E2"

    @app.errorhandler(Exception)
    def handle_exception(e):
        return "Exception"

    @app.route("/E1")
    def raise_e1():
        raise E1

    @app.route("/E3")
    def raise_e3():
        raise E3

    rv = client.get("/E1")
    assert rv.data == b"Exception"

    rv = client.get("/E3")
    assert rv.data == b"E2"


def test_trapping_of_bad_request_key_errors(app, client):
    @app.route("/key")
    def fail():
        flask.request.form["missing_key"]

    @app.route("/abort")
    def allow_abort():
        flask.abort(400)

    rv = client.get("/key")
    assert rv.status_code == 400
    assert b"missing_key" not in rv.data
    rv = client.get("/abort")
    assert rv.status_code == 400

    app.debug = True
    with pytest.raises(KeyError) as e:
        client.get("/key")
    assert e.errisinstance(BadRequest)
    assert "missing_key" in e.value.get_description()
    rv = client.get("/abort")
    assert rv.status_code == 400

    app.debug = False
    app.config["TRAP_BAD_REQUEST_ERRORS"] = True
    with pytest.raises(KeyError):
        client.get("/key")
    with pytest.raises(BadRequest):
        client.get("/abort")


def test_trapping_of_all_http_exceptions(app, client):
    app.config["TRAP_HTTP_EXCEPTIONS"] = True

    @app.route("/fail")
    def fail():
        flask.abort(404)

    with pytest.raises(NotFound):
        client.get("/fail")


def test_error_handler_after_processor_error(app, client):
    app.testing = False

    @app.before_request
    def before_request():
        if _trigger == "before":
            1 // 0

    @app.after_request
    def after_request(response):
        if _trigger == "after":
            1 // 0
        return response

    @app.route("/")
    def index():
        return "Foo"

    @app.errorhandler(500)
    def internal_server_error(e):
        return "Hello Server Error", 500

    for _trigger in "before", "after":
        rv = client.get("/")
        assert rv.status_code == 500
        assert rv.data == b"Hello Server Error"


def test_enctype_debug_helper(app, client):
    from flask.debughelpers import DebugFilesKeyError

    app.debug = True

    @app.route("/fail", methods=["POST"])
    def index():
        return flask.request.files["foo"].filename

    # with statement is important because we leave an exception on the
    # stack otherwise and we want to ensure that this is not the case
    # to not negatively affect other tests.
    with client:
        with pytest.raises(DebugFilesKeyError) as e:
            client.post("/fail", data={"foo": "index.txt"})
        assert "no file contents were transmitted" in str(e.value)
        assert 'This was submitted: "index.txt"' in str(e.value)


def test_response_types(app, client):
    @app.route("/text")
    def from_text():
        return u"Hällo Wörld"

    @app.route("/bytes")
    def from_bytes():
        return u"Hällo Wörld".encode("utf-8")

    @app.route("/full_tuple")
    def from_full_tuple():
        return (
            "Meh",
            400,
            {"X-Foo": "Testing", "Content-Type": "text/plain; charset=utf-8"},
        )

    @app.route("/text_headers")
    def from_text_headers():
        return "Hello", {"X-Foo": "Test", "Content-Type": "text/plain; charset=utf-8"}

    @app.route("/text_status")
    def from_text_status():
        return "Hi, status!", 400

    @app.route("/response_headers")
    def from_response_headers():
        return (
            flask.Response("Hello world", 404, {"X-Foo": "Baz"}),
            {"X-Foo": "Bar", "X-Bar": "Foo"},
        )

    @app.route("/response_status")
    def from_response_status():
        return app.response_class("Hello world", 400), 500

    @app.route("/wsgi")
    def from_wsgi():
        return NotFound()

    @app.route("/dict")
    def from_dict():
        return {"foo": "bar"}, 201

    assert client.get("/text").data == u"Hällo Wörld".encode("utf-8")
    assert client.get("/bytes").data == u"Hällo Wörld".encode("utf-8")

    rv = client.get("/full_tuple")
    assert rv.data == b"Meh"
    assert rv.headers["X-Foo"] == "Testing"
    assert rv.status_code == 400
    assert rv.mimetype == "text/plain"

    rv = client.get("/text_headers")
    assert rv.data == b"Hello"
    assert rv.headers["X-Foo"] == "Test"
    assert rv.status_code == 200
    assert rv.mimetype == "text/plain"

    rv = client.get("/text_status")
    assert rv.data == b"Hi, status!"
    assert rv.status_code == 400
    assert rv.mimetype == "text/html"

    rv = client.get("/response_headers")
    assert rv.data == b"Hello world"
    assert rv.headers.getlist("X-Foo") == ["Baz", "Bar"]
    assert rv.headers["X-Bar"] == "Foo"
    assert rv.status_code == 404

    rv = client.get("/response_status")
    assert rv.data == b"Hello world"
    assert rv.status_code == 500

    rv = client.get("/wsgi")
    assert b"Not Found" in rv.data
    assert rv.status_code == 404

    rv = client.get("/dict")
    assert rv.json == {"foo": "bar"}
    assert rv.status_code == 201


def test_response_type_errors():
    app = flask.Flask(__name__)
    app.testing = True

    @app.route("/none")
    def from_none():
        pass

    @app.route("/small_tuple")
    def from_small_tuple():
        return ("Hello",)

    @app.route("/large_tuple")
    def from_large_tuple():
        return "Hello", 234, {"X-Foo": "Bar"}, "???"

    @app.route("/bad_type")
    def from_bad_type():
        return True

    @app.route("/bad_wsgi")
    def from_bad_wsgi():
        return lambda: None

    c = app.test_client()

    with pytest.raises(TypeError) as e:
        c.get("/none")
        assert "returned None" in str(e.value)

    with pytest.raises(TypeError) as e:
        c.get("/small_tuple")
        assert "tuple must have the form" in str(e.value)

    pytest.raises(TypeError, c.get, "/large_tuple")

    with pytest.raises(TypeError) as e:
        c.get("/bad_type")
        assert "it was a bool" in str(e.value)

    pytest.raises(TypeError, c.get, "/bad_wsgi")


def test_make_response(app, req_ctx):
    rv = flask.make_response()
    assert rv.status_code == 200
    assert rv.data == b""
    assert rv.mimetype == "text/html"

    rv = flask.make_response("Awesome")
    assert rv.status_code == 200
    assert rv.data == b"Awesome"
    assert rv.mimetype == "text/html"

    rv = flask.make_response("W00t", 404)
    assert rv.status_code == 404
    assert rv.data == b"W00t"
    assert rv.mimetype == "text/html"


def test_make_response_with_response_instance(app, req_ctx):
    rv = flask.make_response(flask.jsonify({"msg": "W00t"}), 400)
    assert rv.status_code == 400
    assert rv.data == b'{"msg":"W00t"}\n'
    assert rv.mimetype == "application/json"

    rv = flask.make_response(flask.Response(""), 400)
    assert rv.status_code == 400
    assert rv.data == b""
    assert rv.mimetype == "text/html"

    rv = flask.make_response(
        flask.Response("", headers={"Content-Type": "text/html"}),
        400,
        [("X-Foo", "bar")],
    )
    assert rv.status_code == 400
    assert rv.headers["Content-Type"] == "text/html"
    assert rv.headers["X-Foo"] == "bar"


def test_jsonify_no_prettyprint(app, req_ctx):
    app.config.update({"JSONIFY_PRETTYPRINT_REGULAR": False})
    compressed_msg = b'{"msg":{"submsg":"W00t"},"msg2":"foobar"}\n'
    uncompressed_msg = {"msg": {"submsg": "W00t"}, "msg2": "foobar"}

    rv = flask.make_response(flask.jsonify(uncompressed_msg), 200)
    assert rv.data == compressed_msg


def test_jsonify_prettyprint(app, req_ctx):
    app.config.update({"JSONIFY_PRETTYPRINT_REGULAR": True})
    compressed_msg = {"msg": {"submsg": "W00t"}, "msg2": "foobar"}
    pretty_response = (
        b'{\n  "msg": {\n    "submsg": "W00t"\n  }, \n  "msg2": "foobar"\n}\n'
    )

    rv = flask.make_response(flask.jsonify(compressed_msg), 200)
    assert rv.data == pretty_response


def test_jsonify_mimetype(app, req_ctx):
    app.config.update({"JSONIFY_MIMETYPE": "application/vnd.api+json"})
    msg = {"msg": {"submsg": "W00t"}}
    rv = flask.make_response(flask.jsonify(msg), 200)
    assert rv.mimetype == "application/vnd.api+json"


@pytest.mark.skipif(sys.version_info < (3, 7), reason="requires Python >= 3.7")
def test_json_dump_dataclass(app, req_ctx):
    from dataclasses import make_dataclass

    Data = make_dataclass("Data", [("name", str)])
    value = flask.json.dumps(Data("Flask"), app=app)
    value = flask.json.loads(value, app=app)
    assert value == {"name": "Flask"}


def test_jsonify_args_and_kwargs_check(app, req_ctx):
    with pytest.raises(TypeError) as e:
        flask.jsonify("fake args", kwargs="fake")
    assert "behavior undefined" in str(e.value)


def test_url_generation(app, req_ctx):
    @app.route("/hello/<name>", methods=["POST"])
    def hello():
        pass

    assert flask.url_for("hello", name="test x") == "/hello/test%20x"
    assert (
        flask.url_for("hello", name="test x", _external=True)
        == "http://localhost/hello/test%20x"
    )


def test_build_error_handler(app):
    # Test base case, a URL which results in a BuildError.
    with app.test_request_context():
        pytest.raises(BuildError, flask.url_for, "spam")

    # Verify the error is re-raised if not the current exception.
    try:
        with app.test_request_context():
            flask.url_for("spam")
    except BuildError as err:
        error = err
    try:
        raise RuntimeError("Test case where BuildError is not current.")
    except RuntimeError:
        pytest.raises(BuildError, app.handle_url_build_error, error, "spam", {})

    # Test a custom handler.
    def handler(error, endpoint, values):
        # Just a test.
        return "/test_handler/"

    app.url_build_error_handlers.append(handler)
    with app.test_request_context():
        assert flask.url_for("spam") == "/test_handler/"


def test_build_error_handler_reraise(app):
    # Test a custom handler which reraises the BuildError
    def handler_raises_build_error(error, endpoint, values):
        raise error

    app.url_build_error_handlers.append(handler_raises_build_error)

    with app.test_request_context():
        pytest.raises(BuildError, flask.url_for, "not.existing")


def test_url_for_passes_special_values_to_build_error_handler(app):
    @app.url_build_error_handlers.append
    def handler(error, endpoint, values):
        assert values == {
            "_external": False,
            "_anchor": None,
            "_method": None,
            "_scheme": None,
        }
        return "handled"

    with app.test_request_context():
        flask.url_for("/")


def test_static_files(app, client):
    rv = client.get("/static/index.html")
    assert rv.status_code == 200
    assert rv.data.strip() == b"<h1>Hello World!</h1>"
    with app.test_request_context():
        assert flask.url_for("static", filename="index.html") == "/static/index.html"
    rv.close()


def test_static_url_path():
    app = flask.Flask(__name__, static_url_path="/foo")
    app.testing = True
    rv = app.test_client().get("/foo/index.html")
    assert rv.status_code == 200
    rv.close()

    with app.test_request_context():
        assert flask.url_for("static", filename="index.html") == "/foo/index.html"


def test_static_url_path_with_ending_slash():
    app = flask.Flask(__name__, static_url_path="/foo/")
    app.testing = True
    rv = app.test_client().get("/foo/index.html")
    assert rv.status_code == 200
    rv.close()

    with app.test_request_context():
        assert flask.url_for("static", filename="index.html") == "/foo/index.html"


def test_static_url_empty_path(app):
    app = flask.Flask(__name__, static_folder="", static_url_path="")
    rv = app.test_client().open("/static/index.html", method="GET")
    assert rv.status_code == 200
    rv.close()


def test_static_url_empty_path_default(app):
    app = flask.Flask(__name__, static_folder="")
    rv = app.test_client().open("/static/index.html", method="GET")
    assert rv.status_code == 200
    rv.close()


def test_static_route_with_host_matching():
    app = flask.Flask(__name__, host_matching=True, static_host="example.com")
    c = app.test_client()
    rv = c.get("http://example.com/static/index.html")
    assert rv.status_code == 200
    rv.close()
    with app.test_request_context():
        rv = flask.url_for("static", filename="index.html", _external=True)
        assert rv == "http://example.com/static/index.html"
    # Providing static_host without host_matching=True should error.
    with pytest.raises(Exception):
        flask.Flask(__name__, static_host="example.com")
    # Providing host_matching=True with static_folder
    # but without static_host should error.
    with pytest.raises(Exception):
        flask.Flask(__name__, host_matching=True)
    # Providing host_matching=True without static_host
    # but with static_folder=None should not error.
    flask.Flask(__name__, host_matching=True, static_folder=None)


def test_request_locals():
    assert repr(flask.g) == "<LocalProxy unbound>"
    assert not flask.g


def test_server_name_subdomain():
    app = flask.Flask(__name__, subdomain_matching=True)
    client = app.test_client()

    @app.route("/")
    def index():
        return "default"

    @app.route("/", subdomain="foo")
    def subdomain():
        return "subdomain"

    app.config["SERVER_NAME"] = "dev.local:5000"
    rv = client.get("/")
    assert rv.data == b"default"

    rv = client.get("/", "http://dev.local:5000")
    assert rv.data == b"default"

    rv = client.get("/", "https://dev.local:5000")
    assert rv.data == b"default"

    app.config["SERVER_NAME"] = "dev.local:443"
    rv = client.get("/", "https://dev.local")

    # Werkzeug 1.0 fixes matching https scheme with 443 port
    if rv.status_code != 404:
        assert rv.data == b"default"

    app.config["SERVER_NAME"] = "dev.local"
    rv = client.get("/", "https://dev.local")
    assert rv.data == b"default"

    # suppress Werkzeug 1.0 warning about name mismatch
    with pytest.warns(None):
        rv = client.get("/", "http://foo.localhost")
        assert rv.status_code == 404

    rv = client.get("/", "http://foo.dev.local")
    assert rv.data == b"subdomain"


def test_exception_propagation(app, client):
    def apprunner(config_key):
        @app.route("/")
        def index():
            1 // 0

        if config_key is not None:
            app.config[config_key] = True
            with pytest.raises(Exception):
                client.get("/")
        else:
            assert client.get("/").status_code == 500

    # we have to run this test in an isolated thread because if the
    # debug flag is set to true and an exception happens the context is
    # not torn down.  This causes other tests that run after this fail
    # when they expect no exception on the stack.
    for config_key in "TESTING", "PROPAGATE_EXCEPTIONS", "DEBUG", None:
        t = Thread(target=apprunner, args=(config_key,))
        t.start()
        t.join()


@pytest.mark.parametrize("debug", [True, False])
@pytest.mark.parametrize("use_debugger", [True, False])
@pytest.mark.parametrize("use_reloader", [True, False])
@pytest.mark.parametrize("propagate_exceptions", [None, True, False])
def test_werkzeug_passthrough_errors(
    monkeypatch, debug, use_debugger, use_reloader, propagate_exceptions, app
):
    rv = {}

    # Mocks werkzeug.serving.run_simple method
    def run_simple_mock(*args, **kwargs):
        rv["passthrough_errors"] = kwargs.get("passthrough_errors")

    monkeypatch.setattr(werkzeug.serving, "run_simple", run_simple_mock)
    app.config["PROPAGATE_EXCEPTIONS"] = propagate_exceptions
    app.run(debug=debug, use_debugger=use_debugger, use_reloader=use_reloader)


def test_max_content_length(app, client):
    app.config["MAX_CONTENT_LENGTH"] = 64

    @app.before_request
    def always_first():
        flask.request.form["myfile"]
        AssertionError()

    @app.route("/accept", methods=["POST"])
    def accept_file():
        flask.request.form["myfile"]
        AssertionError()

    @app.errorhandler(413)
    def catcher(error):
        return "42"

    rv = client.post("/accept", data={"myfile": "foo" * 100})
    assert rv.data == b"42"


def test_url_processors(app, client):
    @app.url_defaults
    def add_language_code(endpoint, values):
        if flask.g.lang_code is not None and app.url_map.is_endpoint_expecting(
            endpoint, "lang_code"
        ):
            values.setdefault("lang_code", flask.g.lang_code)

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        flask.g.lang_code = values.pop("lang_code", None)

    @app.route("/<lang_code>/")
    def index():
        return flask.url_for("about")

    @app.route("/<lang_code>/about")
    def about():
        return flask.url_for("something_else")

    @app.route("/foo")
    def something_else():
        return flask.url_for("about", lang_code="en")

    assert client.get("/de/").data == b"/de/about"
    assert client.get("/de/about").data == b"/foo"
    assert client.get("/foo").data == b"/en/about"


def test_inject_blueprint_url_defaults(app):
    bp = flask.Blueprint("foo.bar.baz", __name__, template_folder="template")

    @bp.url_defaults
    def bp_defaults(endpoint, values):
        values["page"] = "login"

    @bp.route("/<page>")
    def view(page):
        pass

    app.register_blueprint(bp)

    values = dict()
    app.inject_url_defaults("foo.bar.baz.view", values)
    expected = dict(page="login")
    assert values == expected

    with app.test_request_context("/somepage"):
        url = flask.url_for("foo.bar.baz.view")
    expected = "/login"
    assert url == expected


def test_nonascii_pathinfo(app, client):
    @app.route(u"/киртест")
    def index():
        return "Hello World!"

    rv = client.get(u"/киртест")
    assert rv.data == b"Hello World!"


def test_debug_mode_complains_after_first_request(app, client):
    app.debug = True

    @app.route("/")
    def index():
        return "Awesome"

    assert not app.got_first_request
    assert client.get("/").data == b"Awesome"
    with pytest.raises(AssertionError) as e:

        @app.route("/foo")
        def broken():
            return "Meh"

    assert "A setup function was called" in str(e.value)

    app.debug = False

    @app.route("/foo")
    def working():
        return "Meh"

    assert client.get("/foo").data == b"Meh"
    assert app.got_first_request


def test_before_first_request_functions(app, client):
    got = []

    @app.before_first_request
    def foo():
        got.append(42)

    client.get("/")
    assert got == [42]
    client.get("/")
    assert got == [42]
    assert app.got_first_request


def test_before_first_request_functions_concurrent(app, client):
    got = []

    @app.before_first_request
    def foo():
        time.sleep(0.2)
        got.append(42)

    def get_and_assert():
        client.get("/")
        assert got == [42]

    t = Thread(target=get_and_assert)
    t.start()
    get_and_assert()
    t.join()
    assert app.got_first_request


def test_routing_redirect_debugging(app, client):
    app.debug = True

    @app.route("/foo/", methods=["GET", "POST"])
    def foo():
        return "success"

    with client:
        with pytest.raises(AssertionError) as e:
            client.post("/foo", data={})
        assert "http://localhost/foo/" in str(e.value)
        assert ("Make sure to directly send your POST-request to this URL") in str(
            e.value
        )

        rv = client.get("/foo", data={}, follow_redirects=True)
        assert rv.data == b"success"

    app.debug = False
    with client:
        rv = client.post("/foo", data={}, follow_redirects=True)
        assert rv.data == b"success"


def test_route_decorator_custom_endpoint(app, client):
    app.debug = True

    @app.route("/foo/")
    def foo():
        return flask.request.endpoint

    @app.route("/bar/", endpoint="bar")
    def for_bar():
        return flask.request.endpoint

    @app.route("/bar/123", endpoint="123")
    def for_bar_foo():
        return flask.request.endpoint

    with app.test_request_context():
        assert flask.url_for("foo") == "/foo/"
        assert flask.url_for("bar") == "/bar/"
        assert flask.url_for("123") == "/bar/123"

    assert client.get("/foo/").data == b"foo"
    assert client.get("/bar/").data == b"bar"
    assert client.get("/bar/123").data == b"123"


def test_preserve_only_once(app, client):
    app.debug = True

    @app.route("/fail")
    def fail_func():
        1 // 0

    for _x in range(3):
        with pytest.raises(ZeroDivisionError):
            client.get("/fail")

    assert flask._request_ctx_stack.top is not None
    assert flask._app_ctx_stack.top is not None
    # implicit appctx disappears too
    flask._request_ctx_stack.top.pop()
    assert flask._request_ctx_stack.top is None
    assert flask._app_ctx_stack.top is None


def test_preserve_remembers_exception(app, client):
    app.debug = True
    errors = []

    @app.route("/fail")
    def fail_func():
        1 // 0

    @app.route("/success")
    def success_func():
        return "Okay"

    @app.teardown_request
    def teardown_handler(exc):
        errors.append(exc)

    # After this failure we did not yet call the teardown handler
    with pytest.raises(ZeroDivisionError):
        client.get("/fail")
    assert errors == []

    # But this request triggers it, and it's an error
    client.get("/success")
    assert len(errors) == 2
    assert isinstance(errors[0], ZeroDivisionError)

    # At this point another request does nothing.
    client.get("/success")
    assert len(errors) == 3
    assert errors[1] is None


def test_get_method_on_g(app_ctx):
    assert flask.g.get("x") is None
    assert flask.g.get("x", 11) == 11
    flask.g.x = 42
    assert flask.g.get("x") == 42
    assert flask.g.x == 42


def test_g_iteration_protocol(app_ctx):
    flask.g.foo = 23
    flask.g.bar = 42
    assert "foo" in flask.g
    assert "foos" not in flask.g
    assert sorted(flask.g) == ["bar", "foo"]


def test_subdomain_basic_support():
    app = flask.Flask(__name__, subdomain_matching=True)
    app.config["SERVER_NAME"] = "localhost.localdomain"
    client = app.test_client()

    @app.route("/")
    def normal_index():
        return "normal index"

    @app.route("/", subdomain="test")
    def test_index():
        return "test index"

    rv = client.get("/", "http://localhost.localdomain/")
    assert rv.data == b"normal index"

    rv = client.get("/", "http://test.localhost.localdomain/")
    assert rv.data == b"test index"


def test_subdomain_matching():
    app = flask.Flask(__name__, subdomain_matching=True)
    client = app.test_client()
    app.config["SERVER_NAME"] = "localhost.localdomain"

    @app.route("/", subdomain="<user>")
    def index(user):
        return "index for %s" % user

    rv = client.get("/", "http://mitsuhiko.localhost.localdomain/")
    assert rv.data == b"index for mitsuhiko"


def test_subdomain_matching_with_ports():
    app = flask.Flask(__name__, subdomain_matching=True)
    app.config["SERVER_NAME"] = "localhost.localdomain:3000"
    client = app.test_client()

    @app.route("/", subdomain="<user>")
    def index(user):
        return "index for %s" % user

    rv = client.get("/", "http://mitsuhiko.localhost.localdomain:3000/")
    assert rv.data == b"index for mitsuhiko"


@pytest.mark.parametrize("matching", (False, True))
def test_subdomain_matching_other_name(matching):
    app = flask.Flask(__name__, subdomain_matching=matching)
    app.config["SERVER_NAME"] = "localhost.localdomain:3000"
    client = app.test_client()

    @app.route("/")
    def index():
        return "", 204

    # suppress Werkzeug 0.15 warning about name mismatch
    with pytest.warns(None):
        # ip address can't match name
        rv = client.get("/", "http://127.0.0.1:3000/")
        assert rv.status_code == 404 if matching else 204

    # allow all subdomains if matching is disabled
    rv = client.get("/", "http://www.localhost.localdomain:3000/")
    assert rv.status_code == 404 if matching else 204


def test_multi_route_rules(app, client):
    @app.route("/")
    @app.route("/<test>/")
    def index(test="a"):
        return test

    rv = client.open("/")
    assert rv.data == b"a"
    rv = client.open("/b/")
    assert rv.data == b"b"


def test_multi_route_class_views(app, client):
    class View(object):
        def __init__(self, app):
            app.add_url_rule("/", "index", self.index)
            app.add_url_rule("/<test>/", "index", self.index)

        def index(self, test="a"):
            return test

    _ = View(app)
    rv = client.open("/")
    assert rv.data == b"a"
    rv = client.open("/b/")
    assert rv.data == b"b"


def test_run_defaults(monkeypatch, app):
    rv = {}

    # Mocks werkzeug.serving.run_simple method
    def run_simple_mock(*args, **kwargs):
        rv["result"] = "running..."

    monkeypatch.setattr(werkzeug.serving, "run_simple", run_simple_mock)
    app.run()
    assert rv["result"] == "running..."


def test_run_server_port(monkeypatch, app):
    rv = {}

    # Mocks werkzeug.serving.run_simple method
    def run_simple_mock(hostname, port, application, *args, **kwargs):
        rv["result"] = "running on %s:%s ..." % (hostname, port)

    monkeypatch.setattr(werkzeug.serving, "run_simple", run_simple_mock)
    hostname, port = "localhost", 8000
    app.run(hostname, port, debug=True)
    assert rv["result"] == "running on %s:%s ..." % (hostname, port)


@pytest.mark.parametrize(
    "host,port,server_name,expect_host,expect_port",
    (
        (None, None, "pocoo.org:8080", "pocoo.org", 8080),
        ("localhost", None, "pocoo.org:8080", "localhost", 8080),
        (None, 80, "pocoo.org:8080", "pocoo.org", 80),
        ("localhost", 80, "pocoo.org:8080", "localhost", 80),
        ("localhost", 0, "localhost:8080", "localhost", 0),
        (None, None, "localhost:8080", "localhost", 8080),
        (None, None, "localhost:0", "localhost", 0),
    ),
)
def test_run_from_config(
    monkeypatch, host, port, server_name, expect_host, expect_port, app
):
    def run_simple_mock(hostname, port, *args, **kwargs):
        assert hostname == expect_host
        assert port == expect_port

    monkeypatch.setattr(werkzeug.serving, "run_simple", run_simple_mock)
    app.config["SERVER_NAME"] = server_name
    app.run(host, port)


def test_max_cookie_size(app, client, recwarn):
    app.config["MAX_COOKIE_SIZE"] = 100

    # outside app context, default to Werkzeug static value,
    # which is also the default config
    response = flask.Response()
    default = flask.Flask.default_config["MAX_COOKIE_SIZE"]
    assert response.max_cookie_size == default

    # inside app context, use app config
    with app.app_context():
        assert flask.Response().max_cookie_size == 100

    @app.route("/")
    def index():
        r = flask.Response("", status=204)
        r.set_cookie("foo", "bar" * 100)
        return r

    client.get("/")
    assert len(recwarn) == 1
    w = recwarn.pop()
    assert "cookie is too large" in str(w.message)

    app.config["MAX_COOKIE_SIZE"] = 0

    client.get("/")
    assert len(recwarn) == 0
