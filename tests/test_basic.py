# -*- coding: utf-8 -*-
"""
    tests.basic
    ~~~~~~~~~~~~~~~~~~~~~

    The basic functionality.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import re
import uuid
import time
import flask
import pickle
from datetime import datetime
from threading import Thread
from flask._compat import text_type
from werkzeug.exceptions import BadRequest, NotFound, Forbidden
from werkzeug.http import parse_date
from werkzeug.routing import BuildError
import werkzeug.serving


def test_options_work():
    app = flask.Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return 'Hello World'
    rv = app.test_client().open('/', method='OPTIONS')
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST']
    assert rv.data == b''


def test_options_on_multiple_rules():
    app = flask.Flask(__name__)

    @app.route('/', methods=['GET', 'POST'])
    def index():
        return 'Hello World'

    @app.route('/', methods=['PUT'])
    def index_put():
        return 'Aha!'
    rv = app.test_client().open('/', method='OPTIONS')
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT']


def test_options_handling_disabled():
    app = flask.Flask(__name__)

    def index():
        return 'Hello World!'
    index.provide_automatic_options = False
    app.route('/')(index)
    rv = app.test_client().open('/', method='OPTIONS')
    assert rv.status_code == 405

    app = flask.Flask(__name__)

    def index2():
        return 'Hello World!'
    index2.provide_automatic_options = True
    app.route('/', methods=['OPTIONS'])(index2)
    rv = app.test_client().open('/', method='OPTIONS')
    assert sorted(rv.allow) == ['OPTIONS']


def test_request_dispatching():
    app = flask.Flask(__name__)

    @app.route('/')
    def index():
        return flask.request.method

    @app.route('/more', methods=['GET', 'POST'])
    def more():
        return flask.request.method

    c = app.test_client()
    assert c.get('/').data == b'GET'
    rv = c.post('/')
    assert rv.status_code == 405
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS']
    rv = c.head('/')
    assert rv.status_code == 200
    assert not rv.data  # head truncates
    assert c.post('/more').data == b'POST'
    assert c.get('/more').data == b'GET'
    rv = c.delete('/more')
    assert rv.status_code == 405
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST']


def test_disallow_string_for_allowed_methods():
    app = flask.Flask(__name__)
    with pytest.raises(TypeError):
        @app.route('/', methods='GET POST')
        def index():
            return "Hey"


def test_url_mapping():
    app = flask.Flask(__name__)

    random_uuid4 = "7eb41166-9ebf-4d26-b771-ea3f54f8b383"

    def index():
        return flask.request.method

    def more():
        return flask.request.method

    def options():
        return random_uuid4


    app.add_url_rule('/', 'index', index)
    app.add_url_rule('/more', 'more', more, methods=['GET', 'POST'])

    # Issue 1288: Test that automatic options are not added when non-uppercase 'options' in methods
    app.add_url_rule('/options', 'options', options, methods=['options'])

    c = app.test_client()
    assert c.get('/').data == b'GET'
    rv = c.post('/')
    assert rv.status_code == 405
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS']
    rv = c.head('/')
    assert rv.status_code == 200
    assert not rv.data  # head truncates
    assert c.post('/more').data == b'POST'
    assert c.get('/more').data == b'GET'
    rv = c.delete('/more')
    assert rv.status_code == 405
    assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST']
    rv = c.open('/options', method='OPTIONS')
    assert rv.status_code == 200
    assert random_uuid4 in rv.data.decode("utf-8")


def test_werkzeug_routing():
    from werkzeug.routing import Submount, Rule
    app = flask.Flask(__name__)
    app.url_map.add(Submount('/foo', [
        Rule('/bar', endpoint='bar'),
        Rule('/', endpoint='index')
    ]))

    def bar():
        return 'bar'

    def index():
        return 'index'
    app.view_functions['bar'] = bar
    app.view_functions['index'] = index

    c = app.test_client()
    assert c.get('/foo/').data == b'index'
    assert c.get('/foo/bar').data == b'bar'


def test_endpoint_decorator():
    from werkzeug.routing import Submount, Rule
    app = flask.Flask(__name__)
    app.url_map.add(Submount('/foo', [
        Rule('/bar', endpoint='bar'),
        Rule('/', endpoint='index')
    ]))

    @app.endpoint('bar')
    def bar():
        return 'bar'

    @app.endpoint('index')
    def index():
        return 'index'

    c = app.test_client()
    assert c.get('/foo/').data == b'index'
    assert c.get('/foo/bar').data == b'bar'


def test_session():
    app = flask.Flask(__name__)
    app.secret_key = 'testkey'

    @app.route('/set', methods=['POST'])
    def set():
        flask.session['value'] = flask.request.form['value']
        return 'value set'

    @app.route('/get')
    def get():
        return flask.session['value']

    c = app.test_client()
    assert c.post('/set', data={'value': '42'}).data == b'value set'
    assert c.get('/get').data == b'42'


def test_session_using_server_name():
    app = flask.Flask(__name__)
    app.config.update(
        SECRET_KEY='foo',
        SERVER_NAME='example.com'
    )

    @app.route('/')
    def index():
        flask.session['testing'] = 42
        return 'Hello World'
    rv = app.test_client().get('/', 'http://example.com/')
    assert 'domain=.example.com' in rv.headers['set-cookie'].lower()
    assert 'httponly' in rv.headers['set-cookie'].lower()


def test_session_using_server_name_and_port():
    app = flask.Flask(__name__)
    app.config.update(
        SECRET_KEY='foo',
        SERVER_NAME='example.com:8080'
    )

    @app.route('/')
    def index():
        flask.session['testing'] = 42
        return 'Hello World'
    rv = app.test_client().get('/', 'http://example.com:8080/')
    assert 'domain=.example.com' in rv.headers['set-cookie'].lower()
    assert 'httponly' in rv.headers['set-cookie'].lower()


def test_session_using_server_name_port_and_path():
    app = flask.Flask(__name__)
    app.config.update(
        SECRET_KEY='foo',
        SERVER_NAME='example.com:8080',
        APPLICATION_ROOT='/foo'
    )

    @app.route('/')
    def index():
        flask.session['testing'] = 42
        return 'Hello World'
    rv = app.test_client().get('/', 'http://example.com:8080/foo')
    assert 'domain=example.com' in rv.headers['set-cookie'].lower()
    assert 'path=/foo' in rv.headers['set-cookie'].lower()
    assert 'httponly' in rv.headers['set-cookie'].lower()


def test_session_using_application_root():
    class PrefixPathMiddleware(object):

        def __init__(self, app, prefix):
            self.app = app
            self.prefix = prefix

        def __call__(self, environ, start_response):
            environ['SCRIPT_NAME'] = self.prefix
            return self.app(environ, start_response)

    app = flask.Flask(__name__)
    app.wsgi_app = PrefixPathMiddleware(app.wsgi_app, '/bar')
    app.config.update(
        SECRET_KEY='foo',
        APPLICATION_ROOT='/bar'
    )

    @app.route('/')
    def index():
        flask.session['testing'] = 42
        return 'Hello World'
    rv = app.test_client().get('/', 'http://example.com:8080/')
    assert 'path=/bar' in rv.headers['set-cookie'].lower()


def test_session_using_session_settings():
    app = flask.Flask(__name__)
    app.config.update(
        SECRET_KEY='foo',
        SERVER_NAME='www.example.com:8080',
        APPLICATION_ROOT='/test',
        SESSION_COOKIE_DOMAIN='.example.com',
        SESSION_COOKIE_HTTPONLY=False,
        SESSION_COOKIE_SECURE=True,
        SESSION_COOKIE_PATH='/'
    )

    @app.route('/')
    def index():
        flask.session['testing'] = 42
        return 'Hello World'
    rv = app.test_client().get('/', 'http://www.example.com:8080/test/')
    cookie = rv.headers['set-cookie'].lower()
    assert 'domain=.example.com' in cookie
    assert 'path=/' in cookie
    assert 'secure' in cookie
    assert 'httponly' not in cookie


def test_missing_session():
    app = flask.Flask(__name__)

    def expect_exception(f, *args, **kwargs):
        e = pytest.raises(RuntimeError, f, *args, **kwargs)
        assert e.value.args and 'session is unavailable' in e.value.args[0]
    with app.test_request_context():
        assert flask.session.get('missing_key') is None
        expect_exception(flask.session.__setitem__, 'foo', 42)
        expect_exception(flask.session.pop, 'foo')


def test_session_expiration():
    permanent = True
    app = flask.Flask(__name__)
    app.secret_key = 'testkey'

    @app.route('/')
    def index():
        flask.session['test'] = 42
        flask.session.permanent = permanent
        return ''

    @app.route('/test')
    def test():
        return text_type(flask.session.permanent)

    client = app.test_client()
    rv = client.get('/')
    assert 'set-cookie' in rv.headers
    match = re.search(r'\bexpires=([^;]+)(?i)', rv.headers['set-cookie'])
    expires = parse_date(match.group())
    expected = datetime.utcnow() + app.permanent_session_lifetime
    assert expires.year == expected.year
    assert expires.month == expected.month
    assert expires.day == expected.day

    rv = client.get('/test')
    assert rv.data == b'True'

    permanent = False
    rv = app.test_client().get('/')
    assert 'set-cookie' in rv.headers
    match = re.search(r'\bexpires=([^;]+)', rv.headers['set-cookie'])
    assert match is None


def test_session_stored_last():
    app = flask.Flask(__name__)
    app.secret_key = 'development-key'
    app.testing = True

    @app.after_request
    def modify_session(response):
        flask.session['foo'] = 42
        return response

    @app.route('/')
    def dump_session_contents():
        return repr(flask.session.get('foo'))

    c = app.test_client()
    assert c.get('/').data == b'None'
    assert c.get('/').data == b'42'


def test_session_special_types():
    app = flask.Flask(__name__)
    app.secret_key = 'development-key'
    app.testing = True
    now = datetime.utcnow().replace(microsecond=0)
    the_uuid = uuid.uuid4()

    @app.after_request
    def modify_session(response):
        flask.session['m'] = flask.Markup('Hello!')
        flask.session['u'] = the_uuid
        flask.session['dt'] = now
        flask.session['b'] = b'\xff'
        flask.session['t'] = (1, 2, 3)
        return response

    @app.route('/')
    def dump_session_contents():
        return pickle.dumps(dict(flask.session))

    c = app.test_client()
    c.get('/')
    rv = pickle.loads(c.get('/').data)
    assert rv['m'] == flask.Markup('Hello!')
    assert type(rv['m']) == flask.Markup
    assert rv['dt'] == now
    assert rv['u'] == the_uuid
    assert rv['b'] == b'\xff'
    assert type(rv['b']) == bytes
    assert rv['t'] == (1, 2, 3)


def test_session_cookie_setting():
    app = flask.Flask(__name__)
    app.testing = True
    app.secret_key = 'dev key'
    is_permanent = True

    @app.route('/bump')
    def bump():
        rv = flask.session['foo'] = flask.session.get('foo', 0) + 1
        flask.session.permanent = is_permanent
        return str(rv)

    @app.route('/read')
    def read():
        return str(flask.session.get('foo', 0))

    def run_test(expect_header):
        with app.test_client() as c:
            assert c.get('/bump').data == b'1'
            assert c.get('/bump').data == b'2'
            assert c.get('/bump').data == b'3'

            rv = c.get('/read')
            set_cookie = rv.headers.get('set-cookie')
            assert (set_cookie is not None) == expect_header
            assert rv.data == b'3'

    is_permanent = True
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    run_test(expect_header=True)

    is_permanent = True
    app.config['SESSION_REFRESH_EACH_REQUEST'] = False
    run_test(expect_header=False)

    is_permanent = False
    app.config['SESSION_REFRESH_EACH_REQUEST'] = True
    run_test(expect_header=False)

    is_permanent = False
    app.config['SESSION_REFRESH_EACH_REQUEST'] = False
    run_test(expect_header=False)


def test_flashes():
    app = flask.Flask(__name__)
    app.secret_key = 'testkey'

    with app.test_request_context():
        assert not flask.session.modified
        flask.flash('Zap')
        flask.session.modified = False
        flask.flash('Zip')
        assert flask.session.modified
        assert list(flask.get_flashed_messages()) == ['Zap', 'Zip']


def test_extended_flashing():
    # Be sure app.testing=True below, else tests can fail silently.
    #
    # Specifically, if app.testing is not set to True, the AssertionErrors
    # in the view functions will cause a 500 response to the test client
    # instead of propagating exceptions.

    app = flask.Flask(__name__)
    app.secret_key = 'testkey'
    app.testing = True

    @app.route('/')
    def index():
        flask.flash(u'Hello World')
        flask.flash(u'Hello World', 'error')
        flask.flash(flask.Markup(u'<em>Testing</em>'), 'warning')
        return ''

    @app.route('/test/')
    def test():
        messages = flask.get_flashed_messages()
        assert list(messages) == [
            u'Hello World',
            u'Hello World',
            flask.Markup(u'<em>Testing</em>')
        ]
        return ''

    @app.route('/test_with_categories/')
    def test_with_categories():
        messages = flask.get_flashed_messages(with_categories=True)
        assert len(messages) == 3
        assert list(messages) == [
            ('message', u'Hello World'),
            ('error', u'Hello World'),
            ('warning', flask.Markup(u'<em>Testing</em>'))
        ]
        return ''

    @app.route('/test_filter/')
    def test_filter():
        messages = flask.get_flashed_messages(
            category_filter=['message'], with_categories=True)
        assert list(messages) == [('message', u'Hello World')]
        return ''

    @app.route('/test_filters/')
    def test_filters():
        messages = flask.get_flashed_messages(
            category_filter=['message', 'warning'], with_categories=True)
        assert list(messages) == [
            ('message', u'Hello World'),
            ('warning', flask.Markup(u'<em>Testing</em>'))
        ]
        return ''

    @app.route('/test_filters_without_returning_categories/')
    def test_filters2():
        messages = flask.get_flashed_messages(
            category_filter=['message', 'warning'])
        assert len(messages) == 2
        assert messages[0] == u'Hello World'
        assert messages[1] == flask.Markup(u'<em>Testing</em>')
        return ''

    # Create new test client on each test to clean flashed messages.

    c = app.test_client()
    c.get('/')
    c.get('/test/')

    c = app.test_client()
    c.get('/')
    c.get('/test_with_categories/')

    c = app.test_client()
    c.get('/')
    c.get('/test_filter/')

    c = app.test_client()
    c.get('/')
    c.get('/test_filters/')

    c = app.test_client()
    c.get('/')
    c.get('/test_filters_without_returning_categories/')


def test_request_processing():
    app = flask.Flask(__name__)
    evts = []

    @app.before_request
    def before_request():
        evts.append('before')

    @app.after_request
    def after_request(response):
        response.data += b'|after'
        evts.append('after')
        return response

    @app.route('/')
    def index():
        assert 'before' in evts
        assert 'after' not in evts
        return 'request'
    assert 'after' not in evts
    rv = app.test_client().get('/').data
    assert 'after' in evts
    assert rv == b'request|after'


def test_request_preprocessing_early_return():
    app = flask.Flask(__name__)
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

    @app.route('/')
    def index():
        evts.append('index')
        return "damnit"

    rv = app.test_client().get('/').data.strip()
    assert rv == b'hello'
    assert evts == [1, 2]


def test_after_request_processing():
    app = flask.Flask(__name__)
    app.testing = True

    @app.route('/')
    def index():
        @flask.after_this_request
        def foo(response):
            response.headers['X-Foo'] = 'a header'
            return response
        return 'Test'
    c = app.test_client()
    resp = c.get('/')
    assert resp.status_code == 200
    assert resp.headers['X-Foo'] == 'a header'


def test_teardown_request_handler():
    called = []
    app = flask.Flask(__name__)

    @app.teardown_request
    def teardown_request(exc):
        called.append(True)
        return "Ignored"

    @app.route('/')
    def root():
        return "Response"
    rv = app.test_client().get('/')
    assert rv.status_code == 200
    assert b'Response' in rv.data
    assert len(called) == 1


def test_teardown_request_handler_debug_mode():
    called = []
    app = flask.Flask(__name__)
    app.testing = True

    @app.teardown_request
    def teardown_request(exc):
        called.append(True)
        return "Ignored"

    @app.route('/')
    def root():
        return "Response"
    rv = app.test_client().get('/')
    assert rv.status_code == 200
    assert b'Response' in rv.data
    assert len(called) == 1


def test_teardown_request_handler_error():
    called = []
    app = flask.Flask(__name__)
    app.config['LOGGER_HANDLER_POLICY'] = 'never'

    @app.teardown_request
    def teardown_request1(exc):
        assert type(exc) == ZeroDivisionError
        called.append(True)
        # This raises a new error and blows away sys.exc_info(), so we can
        # test that all teardown_requests get passed the same original
        # exception.
        try:
            raise TypeError()
        except:
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
        except:
            pass

    @app.route('/')
    def fails():
        1 // 0
    rv = app.test_client().get('/')
    assert rv.status_code == 500
    assert b'Internal Server Error' in rv.data
    assert len(called) == 2


def test_before_after_request_order():
    called = []
    app = flask.Flask(__name__)

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

    @app.route('/')
    def index():
        return '42'
    rv = app.test_client().get('/')
    assert rv.data == b'42'
    assert called == [1, 2, 3, 4, 5, 6]


def test_error_handling():
    app = flask.Flask(__name__)
    app.config['LOGGER_HANDLER_POLICY'] = 'never'

    @app.errorhandler(404)
    def not_found(e):
        return 'not found', 404

    @app.errorhandler(500)
    def internal_server_error(e):
        return 'internal server error', 500

    @app.errorhandler(Forbidden)
    def forbidden(e):
        return 'forbidden', 403

    @app.route('/')
    def index():
        flask.abort(404)

    @app.route('/error')
    def error():
        1 // 0

    @app.route('/forbidden')
    def error2():
        flask.abort(403)
    c = app.test_client()
    rv = c.get('/')
    assert rv.status_code == 404
    assert rv.data == b'not found'
    rv = c.get('/error')
    assert rv.status_code == 500
    assert b'internal server error' == rv.data
    rv = c.get('/forbidden')
    assert rv.status_code == 403
    assert b'forbidden' == rv.data


def test_before_request_and_routing_errors():
    app = flask.Flask(__name__)

    @app.before_request
    def attach_something():
        flask.g.something = 'value'

    @app.errorhandler(404)
    def return_something(error):
        return flask.g.something, 404
    rv = app.test_client().get('/')
    assert rv.status_code == 404
    assert rv.data == b'value'


def test_user_error_handling():
    class MyException(Exception):
        pass

    app = flask.Flask(__name__)

    @app.errorhandler(MyException)
    def handle_my_exception(e):
        assert isinstance(e, MyException)
        return '42'

    @app.route('/')
    def index():
        raise MyException()

    c = app.test_client()
    assert c.get('/').data == b'42'


def test_http_error_subclass_handling():
    class ForbiddenSubclass(Forbidden):
        pass

    app = flask.Flask(__name__)

    @app.errorhandler(ForbiddenSubclass)
    def handle_forbidden_subclass(e):
        assert isinstance(e, ForbiddenSubclass)
        return 'banana'

    @app.errorhandler(403)
    def handle_forbidden_subclass(e):
        assert not isinstance(e, ForbiddenSubclass)
        assert isinstance(e, Forbidden)
        return 'apple'

    @app.route('/1')
    def index1():
        raise ForbiddenSubclass()

    @app.route('/2')
    def index2():
        flask.abort(403)

    @app.route('/3')
    def index3():
        raise Forbidden()

    c = app.test_client()
    assert c.get('/1').data == b'banana'
    assert c.get('/2').data == b'apple'
    assert c.get('/3').data == b'apple'


def test_trapping_of_bad_request_key_errors():
    app = flask.Flask(__name__)
    app.testing = True

    @app.route('/fail')
    def fail():
        flask.request.form['missing_key']
    c = app.test_client()
    assert c.get('/fail').status_code == 400

    app.config['TRAP_BAD_REQUEST_ERRORS'] = True
    c = app.test_client()
    with pytest.raises(KeyError) as e:
        c.get("/fail")
    assert e.errisinstance(BadRequest)


def test_trapping_of_all_http_exceptions():
    app = flask.Flask(__name__)
    app.testing = True
    app.config['TRAP_HTTP_EXCEPTIONS'] = True

    @app.route('/fail')
    def fail():
        flask.abort(404)

    c = app.test_client()
    with pytest.raises(NotFound):
        c.get('/fail')


def test_enctype_debug_helper():
    from flask.debughelpers import DebugFilesKeyError
    app = flask.Flask(__name__)
    app.debug = True

    @app.route('/fail', methods=['POST'])
    def index():
        return flask.request.files['foo'].filename

    # with statement is important because we leave an exception on the
    # stack otherwise and we want to ensure that this is not the case
    # to not negatively affect other tests.
    with app.test_client() as c:
        with pytest.raises(DebugFilesKeyError) as e:
            c.post('/fail', data={'foo': 'index.txt'})
        assert 'no file contents were transmitted' in str(e.value)
        assert 'This was submitted: "index.txt"' in str(e.value)


def test_response_creation():
    app = flask.Flask(__name__)

    @app.route('/unicode')
    def from_unicode():
        return u'Hällo Wörld'

    @app.route('/string')
    def from_string():
        return u'Hällo Wörld'.encode('utf-8')

    @app.route('/args')
    def from_tuple():
        return 'Meh', 400, {
            'X-Foo': 'Testing',
            'Content-Type': 'text/plain; charset=utf-8'
        }

    @app.route('/two_args')
    def from_two_args_tuple():
        return 'Hello', {
            'X-Foo': 'Test',
            'Content-Type': 'text/plain; charset=utf-8'
        }

    @app.route('/args_status')
    def from_status_tuple():
        return 'Hi, status!', 400

    @app.route('/args_header')
    def from_response_instance_status_tuple():
        return flask.Response('Hello world', 404), {
            "X-Foo": "Bar",
            "X-Bar": "Foo"
        }

    c = app.test_client()
    assert c.get('/unicode').data == u'Hällo Wörld'.encode('utf-8')
    assert c.get('/string').data == u'Hällo Wörld'.encode('utf-8')
    rv = c.get('/args')
    assert rv.data == b'Meh'
    assert rv.headers['X-Foo'] == 'Testing'
    assert rv.status_code == 400
    assert rv.mimetype == 'text/plain'
    rv2 = c.get('/two_args')
    assert rv2.data == b'Hello'
    assert rv2.headers['X-Foo'] == 'Test'
    assert rv2.status_code == 200
    assert rv2.mimetype == 'text/plain'
    rv3 = c.get('/args_status')
    assert rv3.data == b'Hi, status!'
    assert rv3.status_code == 400
    assert rv3.mimetype == 'text/html'
    rv4 = c.get('/args_header')
    assert rv4.data == b'Hello world'
    assert rv4.headers['X-Foo'] == 'Bar'
    assert rv4.headers['X-Bar'] == 'Foo'
    assert rv4.status_code == 404


def test_make_response():
    app = flask.Flask(__name__)
    with app.test_request_context():
        rv = flask.make_response()
        assert rv.status_code == 200
        assert rv.data == b''
        assert rv.mimetype == 'text/html'

        rv = flask.make_response('Awesome')
        assert rv.status_code == 200
        assert rv.data == b'Awesome'
        assert rv.mimetype == 'text/html'

        rv = flask.make_response('W00t', 404)
        assert rv.status_code == 404
        assert rv.data == b'W00t'
        assert rv.mimetype == 'text/html'


def test_make_response_with_response_instance():
    app = flask.Flask(__name__)
    with app.test_request_context():
        rv = flask.make_response(
            flask.jsonify({'msg': 'W00t'}), 400)
        assert rv.status_code == 400
        assert rv.data == b'{\n  "msg": "W00t"\n}\n'
        assert rv.mimetype == 'application/json'

        rv = flask.make_response(
            flask.Response(''), 400)
        assert rv.status_code == 400
        assert rv.data == b''
        assert rv.mimetype == 'text/html'

        rv = flask.make_response(
            flask.Response('', headers={'Content-Type': 'text/html'}),
            400, [('X-Foo', 'bar')])
        assert rv.status_code == 400
        assert rv.headers['Content-Type'] == 'text/html'
        assert rv.headers['X-Foo'] == 'bar'


def test_jsonify_no_prettyprint():
    app = flask.Flask(__name__)
    app.config.update({"JSONIFY_PRETTYPRINT_REGULAR": False})
    with app.test_request_context():
        compressed_msg = b'{"msg":{"submsg":"W00t"},"msg2":"foobar"}\n'
        uncompressed_msg = {
            "msg": {
                "submsg": "W00t"
            },
            "msg2": "foobar"
            }

        rv = flask.make_response(
            flask.jsonify(uncompressed_msg), 200)
        assert rv.data == compressed_msg


def test_jsonify_prettyprint():
    app = flask.Flask(__name__)
    app.config.update({"JSONIFY_PRETTYPRINT_REGULAR": True})
    with app.test_request_context():
        compressed_msg = {"msg":{"submsg":"W00t"},"msg2":"foobar"}
        pretty_response =\
            b'{\n  "msg": {\n    "submsg": "W00t"\n  }, \n  "msg2": "foobar"\n}\n'

        rv = flask.make_response(
            flask.jsonify(compressed_msg), 200)
        assert rv.data == pretty_response


def test_jsonify_mimetype():
    app = flask.Flask(__name__)
    app.config.update({"JSONIFY_MIMETYPE": 'application/vnd.api+json'})
    with app.test_request_context():
        msg = {
            "msg": {"submsg": "W00t"},
        }
        rv = flask.make_response(
            flask.jsonify(msg), 200)
        assert rv.mimetype == 'application/vnd.api+json'


def test_jsonify_args_and_kwargs_check():
    app = flask.Flask(__name__)
    with app.test_request_context():
        with pytest.raises(TypeError) as e:
            flask.jsonify('fake args', kwargs='fake')
        assert 'behavior undefined' in str(e.value)


def test_url_generation():
    app = flask.Flask(__name__)

    @app.route('/hello/<name>', methods=['POST'])
    def hello():
        pass
    with app.test_request_context():
        assert flask.url_for('hello', name='test x') == '/hello/test%20x'
        assert flask.url_for('hello', name='test x', _external=True) == \
            'http://localhost/hello/test%20x'


def test_build_error_handler():
    app = flask.Flask(__name__)

    # Test base case, a URL which results in a BuildError.
    with app.test_request_context():
        pytest.raises(BuildError, flask.url_for, 'spam')

    # Verify the error is re-raised if not the current exception.
    try:
        with app.test_request_context():
            flask.url_for('spam')
    except BuildError as err:
        error = err
    try:
        raise RuntimeError('Test case where BuildError is not current.')
    except RuntimeError:
        pytest.raises(
            BuildError, app.handle_url_build_error, error, 'spam', {})

    # Test a custom handler.
    def handler(error, endpoint, values):
        # Just a test.
        return '/test_handler/'
    app.url_build_error_handlers.append(handler)
    with app.test_request_context():
        assert flask.url_for('spam') == '/test_handler/'


def test_build_error_handler_reraise():
    app = flask.Flask(__name__)

    # Test a custom handler which reraises the BuildError
    def handler_raises_build_error(error, endpoint, values):
        raise error
    app.url_build_error_handlers.append(handler_raises_build_error)

    with app.test_request_context():
        pytest.raises(BuildError, flask.url_for, 'not.existing')


def test_custom_converters():
    from werkzeug.routing import BaseConverter

    class ListConverter(BaseConverter):

        def to_python(self, value):
            return value.split(',')

        def to_url(self, value):
            base_to_url = super(ListConverter, self).to_url
            return ','.join(base_to_url(x) for x in value)
    app = flask.Flask(__name__)
    app.url_map.converters['list'] = ListConverter

    @app.route('/<list:args>')
    def index(args):
        return '|'.join(args)
    c = app.test_client()
    assert c.get('/1,2,3').data == b'1|2|3'


def test_static_files():
    app = flask.Flask(__name__)
    app.testing = True
    rv = app.test_client().get('/static/index.html')
    assert rv.status_code == 200
    assert rv.data.strip() == b'<h1>Hello World!</h1>'
    with app.test_request_context():
        assert flask.url_for('static', filename='index.html') == \
            '/static/index.html'
    rv.close()


def test_static_path_deprecated(recwarn):
    app = flask.Flask(__name__, static_path='/foo')
    recwarn.pop(DeprecationWarning)

    app.testing = True
    rv = app.test_client().get('/foo/index.html')
    assert rv.status_code == 200
    rv.close()

    with app.test_request_context():
        assert flask.url_for('static', filename='index.html') == '/foo/index.html'


def test_static_url_path():
    app = flask.Flask(__name__, static_url_path='/foo')
    app.testing = True
    rv = app.test_client().get('/foo/index.html')
    assert rv.status_code == 200
    rv.close()

    with app.test_request_context():
        assert flask.url_for('static', filename='index.html') == '/foo/index.html'


def test_none_response():
    app = flask.Flask(__name__)
    app.testing = True

    @app.route('/')
    def test():
        return None
    try:
        app.test_client().get('/')
    except ValueError as e:
        assert str(e) == 'View function did not return a response'
        pass
    else:
        assert "Expected ValueError"


def test_request_locals():
    assert repr(flask.g) == '<LocalProxy unbound>'
    assert not flask.g


def test_test_app_proper_environ():
    app = flask.Flask(__name__)
    app.config.update(
        SERVER_NAME='localhost.localdomain:5000'
    )

    @app.route('/')
    def index():
        return 'Foo'

    @app.route('/', subdomain='foo')
    def subdomain():
        return 'Foo SubDomain'

    rv = app.test_client().get('/')
    assert rv.data == b'Foo'

    rv = app.test_client().get('/', 'http://localhost.localdomain:5000')
    assert rv.data == b'Foo'

    rv = app.test_client().get('/', 'https://localhost.localdomain:5000')
    assert rv.data == b'Foo'

    app.config.update(SERVER_NAME='localhost.localdomain')
    rv = app.test_client().get('/', 'https://localhost.localdomain')
    assert rv.data == b'Foo'

    try:
        app.config.update(SERVER_NAME='localhost.localdomain:443')
        rv = app.test_client().get('/', 'https://localhost.localdomain')
        # Werkzeug 0.8
        assert rv.status_code == 404
    except ValueError as e:
        # Werkzeug 0.7
        assert str(e) == (
            "the server name provided "
            "('localhost.localdomain:443') does not match the "
            "server name from the WSGI environment ('localhost.localdomain')"
        )

    try:
        app.config.update(SERVER_NAME='localhost.localdomain')
        rv = app.test_client().get('/', 'http://foo.localhost')
        # Werkzeug 0.8
        assert rv.status_code == 404
    except ValueError as e:
        # Werkzeug 0.7
        assert str(e) == (
            "the server name provided "
            "('localhost.localdomain') does not match the "
            "server name from the WSGI environment ('foo.localhost')"
        )

    rv = app.test_client().get('/', 'http://foo.localhost.localdomain')
    assert rv.data == b'Foo SubDomain'


def test_exception_propagation():
    def apprunner(config_key):
        app = flask.Flask(__name__)
        app.config['LOGGER_HANDLER_POLICY'] = 'never'

        @app.route('/')
        def index():
            1 // 0
        c = app.test_client()
        if config_key is not None:
            app.config[config_key] = True
            with pytest.raises(Exception):
                c.get('/')
        else:
            assert c.get('/').status_code == 500

    # we have to run this test in an isolated thread because if the
    # debug flag is set to true and an exception happens the context is
    # not torn down.  This causes other tests that run after this fail
    # when they expect no exception on the stack.
    for config_key in 'TESTING', 'PROPAGATE_EXCEPTIONS', 'DEBUG', None:
        t = Thread(target=apprunner, args=(config_key,))
        t.start()
        t.join()


@pytest.mark.parametrize('debug', [True, False])
@pytest.mark.parametrize('use_debugger', [True, False])
@pytest.mark.parametrize('use_reloader', [True, False])
@pytest.mark.parametrize('propagate_exceptions', [None, True, False])
def test_werkzeug_passthrough_errors(monkeypatch, debug, use_debugger,
                                     use_reloader, propagate_exceptions):
    rv = {}

    # Mocks werkzeug.serving.run_simple method
    def run_simple_mock(*args, **kwargs):
        rv['passthrough_errors'] = kwargs.get('passthrough_errors')

    app = flask.Flask(__name__)
    monkeypatch.setattr(werkzeug.serving, 'run_simple', run_simple_mock)
    app.config['PROPAGATE_EXCEPTIONS'] = propagate_exceptions
    app.run(debug=debug, use_debugger=use_debugger, use_reloader=use_reloader)
    # make sure werkzeug always passes errors through
    assert rv['passthrough_errors']


def test_max_content_length():
    app = flask.Flask(__name__)
    app.config['MAX_CONTENT_LENGTH'] = 64

    @app.before_request
    def always_first():
        flask.request.form['myfile']
        assert False

    @app.route('/accept', methods=['POST'])
    def accept_file():
        flask.request.form['myfile']
        assert False

    @app.errorhandler(413)
    def catcher(error):
        return '42'

    c = app.test_client()
    rv = c.post('/accept', data={'myfile': 'foo' * 100})
    assert rv.data == b'42'


def test_url_processors():
    app = flask.Flask(__name__)

    @app.url_defaults
    def add_language_code(endpoint, values):
        if flask.g.lang_code is not None and \
           app.url_map.is_endpoint_expecting(endpoint, 'lang_code'):
            values.setdefault('lang_code', flask.g.lang_code)

    @app.url_value_preprocessor
    def pull_lang_code(endpoint, values):
        flask.g.lang_code = values.pop('lang_code', None)

    @app.route('/<lang_code>/')
    def index():
        return flask.url_for('about')

    @app.route('/<lang_code>/about')
    def about():
        return flask.url_for('something_else')

    @app.route('/foo')
    def something_else():
        return flask.url_for('about', lang_code='en')

    c = app.test_client()

    assert c.get('/de/').data == b'/de/about'
    assert c.get('/de/about').data == b'/foo'
    assert c.get('/foo').data == b'/en/about'


def test_inject_blueprint_url_defaults():
    app = flask.Flask(__name__)
    bp = flask.Blueprint('foo.bar.baz', __name__,
                         template_folder='template')

    @bp.url_defaults
    def bp_defaults(endpoint, values):
        values['page'] = 'login'

    @bp.route('/<page>')
    def view(page):
        pass

    app.register_blueprint(bp)

    values = dict()
    app.inject_url_defaults('foo.bar.baz.view', values)
    expected = dict(page='login')
    assert values == expected

    with app.test_request_context('/somepage'):
        url = flask.url_for('foo.bar.baz.view')
    expected = '/login'
    assert url == expected


def test_nonascii_pathinfo():
    app = flask.Flask(__name__)
    app.testing = True

    @app.route(u'/киртест')
    def index():
        return 'Hello World!'

    c = app.test_client()
    rv = c.get(u'/киртест')
    assert rv.data == b'Hello World!'


def test_debug_mode_complains_after_first_request():
    app = flask.Flask(__name__)
    app.debug = True

    @app.route('/')
    def index():
        return 'Awesome'
    assert not app.got_first_request
    assert app.test_client().get('/').data == b'Awesome'
    with pytest.raises(AssertionError) as e:
        @app.route('/foo')
        def broken():
            return 'Meh'
    assert 'A setup function was called' in str(e)

    app.debug = False

    @app.route('/foo')
    def working():
        return 'Meh'
    assert app.test_client().get('/foo').data == b'Meh'
    assert app.got_first_request


def test_before_first_request_functions():
    got = []
    app = flask.Flask(__name__)

    @app.before_first_request
    def foo():
        got.append(42)
    c = app.test_client()
    c.get('/')
    assert got == [42]
    c.get('/')
    assert got == [42]
    assert app.got_first_request


def test_before_first_request_functions_concurrent():
    got = []
    app = flask.Flask(__name__)

    @app.before_first_request
    def foo():
        time.sleep(0.2)
        got.append(42)

    c = app.test_client()

    def get_and_assert():
        c.get("/")
        assert got == [42]

    t = Thread(target=get_and_assert)
    t.start()
    get_and_assert()
    t.join()
    assert app.got_first_request


def test_routing_redirect_debugging():
    app = flask.Flask(__name__)
    app.debug = True

    @app.route('/foo/', methods=['GET', 'POST'])
    def foo():
        return 'success'
    with app.test_client() as c:
        with pytest.raises(AssertionError) as e:
            c.post('/foo', data={})
        assert 'http://localhost/foo/' in str(e)
        assert ('Make sure to directly send '
                'your POST-request to this URL') in str(e)

        rv = c.get('/foo', data={}, follow_redirects=True)
        assert rv.data == b'success'

    app.debug = False
    with app.test_client() as c:
        rv = c.post('/foo', data={}, follow_redirects=True)
        assert rv.data == b'success'


def test_route_decorator_custom_endpoint():
    app = flask.Flask(__name__)
    app.debug = True

    @app.route('/foo/')
    def foo():
        return flask.request.endpoint

    @app.route('/bar/', endpoint='bar')
    def for_bar():
        return flask.request.endpoint

    @app.route('/bar/123', endpoint='123')
    def for_bar_foo():
        return flask.request.endpoint

    with app.test_request_context():
        assert flask.url_for('foo') == '/foo/'
        assert flask.url_for('bar') == '/bar/'
        assert flask.url_for('123') == '/bar/123'

    c = app.test_client()
    assert c.get('/foo/').data == b'foo'
    assert c.get('/bar/').data == b'bar'
    assert c.get('/bar/123').data == b'123'


def test_preserve_only_once():
    app = flask.Flask(__name__)
    app.debug = True

    @app.route('/fail')
    def fail_func():
        1 // 0

    c = app.test_client()
    for x in range(3):
        with pytest.raises(ZeroDivisionError):
            c.get('/fail')

    assert flask._request_ctx_stack.top is not None
    assert flask._app_ctx_stack.top is not None
    # implicit appctx disappears too
    flask._request_ctx_stack.top.pop()
    assert flask._request_ctx_stack.top is None
    assert flask._app_ctx_stack.top is None


def test_preserve_remembers_exception():
    app = flask.Flask(__name__)
    app.debug = True
    errors = []

    @app.route('/fail')
    def fail_func():
        1 // 0

    @app.route('/success')
    def success_func():
        return 'Okay'

    @app.teardown_request
    def teardown_handler(exc):
        errors.append(exc)

    c = app.test_client()

    # After this failure we did not yet call the teardown handler
    with pytest.raises(ZeroDivisionError):
        c.get('/fail')
    assert errors == []

    # But this request triggers it, and it's an error
    c.get('/success')
    assert len(errors) == 2
    assert isinstance(errors[0], ZeroDivisionError)

    # At this point another request does nothing.
    c.get('/success')
    assert len(errors) == 3
    assert errors[1] is None


def test_get_method_on_g():
    app = flask.Flask(__name__)
    app.testing = True

    with app.app_context():
        assert flask.g.get('x') is None
        assert flask.g.get('x', 11) == 11
        flask.g.x = 42
        assert flask.g.get('x') == 42
        assert flask.g.x == 42


def test_g_iteration_protocol():
    app = flask.Flask(__name__)
    app.testing = True

    with app.app_context():
        flask.g.foo = 23
        flask.g.bar = 42
        assert 'foo' in flask.g
        assert 'foos' not in flask.g
        assert sorted(flask.g) == ['bar', 'foo']


def test_subdomain_basic_support():
    app = flask.Flask(__name__)
    app.config['SERVER_NAME'] = 'localhost'

    @app.route('/')
    def normal_index():
        return 'normal index'

    @app.route('/', subdomain='test')
    def test_index():
        return 'test index'

    c = app.test_client()
    rv = c.get('/', 'http://localhost/')
    assert rv.data == b'normal index'

    rv = c.get('/', 'http://test.localhost/')
    assert rv.data == b'test index'


def test_subdomain_matching():
    app = flask.Flask(__name__)
    app.config['SERVER_NAME'] = 'localhost'

    @app.route('/', subdomain='<user>')
    def index(user):
        return 'index for %s' % user

    c = app.test_client()
    rv = c.get('/', 'http://mitsuhiko.localhost/')
    assert rv.data == b'index for mitsuhiko'


def test_subdomain_matching_with_ports():
    app = flask.Flask(__name__)
    app.config['SERVER_NAME'] = 'localhost:3000'

    @app.route('/', subdomain='<user>')
    def index(user):
        return 'index for %s' % user

    c = app.test_client()
    rv = c.get('/', 'http://mitsuhiko.localhost:3000/')
    assert rv.data == b'index for mitsuhiko'


def test_multi_route_rules():
    app = flask.Flask(__name__)

    @app.route('/')
    @app.route('/<test>/')
    def index(test='a'):
        return test

    rv = app.test_client().open('/')
    assert rv.data == b'a'
    rv = app.test_client().open('/b/')
    assert rv.data == b'b'


def test_multi_route_class_views():
    class View(object):

        def __init__(self, app):
            app.add_url_rule('/', 'index', self.index)
            app.add_url_rule('/<test>/', 'index', self.index)

        def index(self, test='a'):
            return test

    app = flask.Flask(__name__)
    _ = View(app)
    rv = app.test_client().open('/')
    assert rv.data == b'a'
    rv = app.test_client().open('/b/')
    assert rv.data == b'b'


def test_run_defaults(monkeypatch):
    rv = {}

    # Mocks werkzeug.serving.run_simple method
    def run_simple_mock(*args, **kwargs):
        rv['result'] = 'running...'

    app = flask.Flask(__name__)
    monkeypatch.setattr(werkzeug.serving, 'run_simple', run_simple_mock)
    app.run()
    assert rv['result'] == 'running...'


def test_run_server_port(monkeypatch):
    rv = {}

    # Mocks werkzeug.serving.run_simple method
    def run_simple_mock(hostname, port, application, *args, **kwargs):
        rv['result'] = 'running on %s:%s ...' % (hostname, port)

    app = flask.Flask(__name__)
    monkeypatch.setattr(werkzeug.serving, 'run_simple', run_simple_mock)
    hostname, port = 'localhost', 8000
    app.run(hostname, port, debug=True)
    assert rv['result'] == 'running on %s:%s ...' % (hostname, port)
