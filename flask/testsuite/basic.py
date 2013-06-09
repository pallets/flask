# -*- coding: utf-8 -*-
"""
    flask.testsuite.basic
    ~~~~~~~~~~~~~~~~~~~~~

    The basic functionality.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import re
import uuid
import flask
import pickle
import unittest
from datetime import datetime
from threading import Thread
from flask.testsuite import FlaskTestCase, emits_module_deprecation_warning
from flask._compat import text_type
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.http import parse_date
from werkzeug.routing import BuildError


class BasicFunctionalityTestCase(FlaskTestCase):

    def test_options_work(self):
        app = flask.Flask(__name__)
        @app.route('/', methods=['GET', 'POST'])
        def index():
            return 'Hello World'
        rv = app.test_client().open('/', method='OPTIONS')
        self.assert_equal(sorted(rv.allow), ['GET', 'HEAD', 'OPTIONS', 'POST'])
        self.assert_equal(rv.data, b'')

    def test_options_on_multiple_rules(self):
        app = flask.Flask(__name__)
        @app.route('/', methods=['GET', 'POST'])
        def index():
            return 'Hello World'
        @app.route('/', methods=['PUT'])
        def index_put():
            return 'Aha!'
        rv = app.test_client().open('/', method='OPTIONS')
        self.assert_equal(sorted(rv.allow), ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT'])

    def test_options_handling_disabled(self):
        app = flask.Flask(__name__)
        def index():
            return 'Hello World!'
        index.provide_automatic_options = False
        app.route('/')(index)
        rv = app.test_client().open('/', method='OPTIONS')
        self.assert_equal(rv.status_code, 405)

        app = flask.Flask(__name__)
        def index2():
            return 'Hello World!'
        index2.provide_automatic_options = True
        app.route('/', methods=['OPTIONS'])(index2)
        rv = app.test_client().open('/', method='OPTIONS')
        self.assert_equal(sorted(rv.allow), ['OPTIONS'])

    def test_request_dispatching(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.request.method
        @app.route('/more', methods=['GET', 'POST'])
        def more():
            return flask.request.method

        c = app.test_client()
        self.assert_equal(c.get('/').data, b'GET')
        rv = c.post('/')
        self.assert_equal(rv.status_code, 405)
        self.assert_equal(sorted(rv.allow), ['GET', 'HEAD', 'OPTIONS'])
        rv = c.head('/')
        self.assert_equal(rv.status_code, 200)
        self.assert_false(rv.data) # head truncates
        self.assert_equal(c.post('/more').data, b'POST')
        self.assert_equal(c.get('/more').data, b'GET')
        rv = c.delete('/more')
        self.assert_equal(rv.status_code, 405)
        self.assert_equal(sorted(rv.allow), ['GET', 'HEAD', 'OPTIONS', 'POST'])

    def test_url_mapping(self):
        app = flask.Flask(__name__)
        def index():
            return flask.request.method
        def more():
            return flask.request.method

        app.add_url_rule('/', 'index', index)
        app.add_url_rule('/more', 'more', more, methods=['GET', 'POST'])

        c = app.test_client()
        self.assert_equal(c.get('/').data, b'GET')
        rv = c.post('/')
        self.assert_equal(rv.status_code, 405)
        self.assert_equal(sorted(rv.allow), ['GET', 'HEAD', 'OPTIONS'])
        rv = c.head('/')
        self.assert_equal(rv.status_code, 200)
        self.assert_false(rv.data) # head truncates
        self.assert_equal(c.post('/more').data, b'POST')
        self.assert_equal(c.get('/more').data, b'GET')
        rv = c.delete('/more')
        self.assert_equal(rv.status_code, 405)
        self.assert_equal(sorted(rv.allow), ['GET', 'HEAD', 'OPTIONS', 'POST'])

    def test_werkzeug_routing(self):
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
        self.assert_equal(c.get('/foo/').data, b'index')
        self.assert_equal(c.get('/foo/bar').data, b'bar')

    def test_endpoint_decorator(self):
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
        self.assert_equal(c.get('/foo/').data, b'index')
        self.assert_equal(c.get('/foo/bar').data, b'bar')

    def test_session(self):
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
        self.assert_equal(c.post('/set', data={'value': '42'}).data, b'value set')
        self.assert_equal(c.get('/get').data, b'42')

    def test_session_using_server_name(self):
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
        self.assert_in('domain=.example.com', rv.headers['set-cookie'].lower())
        self.assert_in('httponly', rv.headers['set-cookie'].lower())

    def test_session_using_server_name_and_port(self):
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
        self.assert_in('domain=.example.com', rv.headers['set-cookie'].lower())
        self.assert_in('httponly', rv.headers['set-cookie'].lower())

    def test_session_using_server_name_port_and_path(self):
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
        self.assert_in('domain=example.com', rv.headers['set-cookie'].lower())
        self.assert_in('path=/foo', rv.headers['set-cookie'].lower())
        self.assert_in('httponly', rv.headers['set-cookie'].lower())

    def test_session_using_application_root(self):
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
        self.assert_in('path=/bar', rv.headers['set-cookie'].lower())

    def test_session_using_session_settings(self):
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
        self.assert_in('domain=.example.com', cookie)
        self.assert_in('path=/', cookie)
        self.assert_in('secure', cookie)
        self.assert_not_in('httponly', cookie)

    def test_missing_session(self):
        app = flask.Flask(__name__)
        def expect_exception(f, *args, **kwargs):
            try:
                f(*args, **kwargs)
            except RuntimeError as e:
                self.assert_true(e.args and 'session is unavailable' in e.args[0])
            else:
                self.assert_true(False, 'expected exception')
        with app.test_request_context():
            self.assert_true(flask.session.get('missing_key') is None)
            expect_exception(flask.session.__setitem__, 'foo', 42)
            expect_exception(flask.session.pop, 'foo')

    def test_session_expiration(self):
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
        self.assert_in('set-cookie', rv.headers)
        match = re.search(r'\bexpires=([^;]+)(?i)', rv.headers['set-cookie'])
        expires = parse_date(match.group())
        expected = datetime.utcnow() + app.permanent_session_lifetime
        self.assert_equal(expires.year, expected.year)
        self.assert_equal(expires.month, expected.month)
        self.assert_equal(expires.day, expected.day)

        rv = client.get('/test')
        self.assert_equal(rv.data, b'True')

        permanent = False
        rv = app.test_client().get('/')
        self.assert_in('set-cookie', rv.headers)
        match = re.search(r'\bexpires=([^;]+)', rv.headers['set-cookie'])
        self.assert_true(match is None)

    def test_session_stored_last(self):
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
        self.assert_equal(c.get('/').data, b'None')
        self.assert_equal(c.get('/').data, b'42')

    def test_session_special_types(self):
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
            flask.session['t'] = (1, 2, 3)
            return response

        @app.route('/')
        def dump_session_contents():
            return pickle.dumps(dict(flask.session))

        c = app.test_client()
        c.get('/')
        rv = pickle.loads(c.get('/').data)
        self.assert_equal(rv['m'], flask.Markup('Hello!'))
        self.assert_equal(type(rv['m']), flask.Markup)
        self.assert_equal(rv['dt'], now)
        self.assert_equal(rv['u'], the_uuid)
        self.assert_equal(rv['t'], (1, 2, 3))

    def test_flashes(self):
        app = flask.Flask(__name__)
        app.secret_key = 'testkey'

        with app.test_request_context():
            self.assert_false(flask.session.modified)
            flask.flash('Zap')
            flask.session.modified = False
            flask.flash('Zip')
            self.assert_true(flask.session.modified)
            self.assert_equal(list(flask.get_flashed_messages()), ['Zap', 'Zip'])

    def test_extended_flashing(self):
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
            self.assert_equal(len(messages), 3)
            self.assert_equal(messages[0], u'Hello World')
            self.assert_equal(messages[1], u'Hello World')
            self.assert_equal(messages[2], flask.Markup(u'<em>Testing</em>'))
            return ''

        @app.route('/test_with_categories/')
        def test_with_categories():
            messages = flask.get_flashed_messages(with_categories=True)
            self.assert_equal(len(messages), 3)
            self.assert_equal(messages[0], ('message', u'Hello World'))
            self.assert_equal(messages[1], ('error', u'Hello World'))
            self.assert_equal(messages[2], ('warning', flask.Markup(u'<em>Testing</em>')))
            return ''

        @app.route('/test_filter/')
        def test_filter():
            messages = flask.get_flashed_messages(category_filter=['message'], with_categories=True)
            self.assert_equal(len(messages), 1)
            self.assert_equal(messages[0], ('message', u'Hello World'))
            return ''

        @app.route('/test_filters/')
        def test_filters():
            messages = flask.get_flashed_messages(category_filter=['message', 'warning'], with_categories=True)
            self.assert_equal(len(messages), 2)
            self.assert_equal(messages[0], ('message', u'Hello World'))
            self.assert_equal(messages[1], ('warning', flask.Markup(u'<em>Testing</em>')))
            return ''

        @app.route('/test_filters_without_returning_categories/')
        def test_filters2():
            messages = flask.get_flashed_messages(category_filter=['message', 'warning'])
            self.assert_equal(len(messages), 2)
            self.assert_equal(messages[0], u'Hello World')
            self.assert_equal(messages[1], flask.Markup(u'<em>Testing</em>'))
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

    def test_request_processing(self):
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
            self.assert_in('before', evts)
            self.assert_not_in('after', evts)
            return 'request'
        self.assert_not_in('after', evts)
        rv = app.test_client().get('/').data
        self.assert_in('after', evts)
        self.assert_equal(rv, b'request|after')

    def test_after_request_processing(self):
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
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(resp.headers['X-Foo'], 'a header')

    def test_teardown_request_handler(self):
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
        self.assert_equal(rv.status_code, 200)
        self.assert_in(b'Response', rv.data)
        self.assert_equal(len(called), 1)

    def test_teardown_request_handler_debug_mode(self):
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
        self.assert_equal(rv.status_code, 200)
        self.assert_in(b'Response', rv.data)
        self.assert_equal(len(called), 1)

    def test_teardown_request_handler_error(self):
        called = []
        app = flask.Flask(__name__)
        @app.teardown_request
        def teardown_request1(exc):
            self.assert_equal(type(exc), ZeroDivisionError)
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
            self.assert_equal(type(exc), ZeroDivisionError)
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
        self.assert_equal(rv.status_code, 500)
        self.assert_in(b'Internal Server Error', rv.data)
        self.assert_equal(len(called), 2)

    def test_before_after_request_order(self):
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
        self.assert_equal(rv.data, b'42')
        self.assert_equal(called, [1, 2, 3, 4, 5, 6])

    def test_error_handling(self):
        app = flask.Flask(__name__)
        @app.errorhandler(404)
        def not_found(e):
            return 'not found', 404
        @app.errorhandler(500)
        def internal_server_error(e):
            return 'internal server error', 500
        @app.route('/')
        def index():
            flask.abort(404)
        @app.route('/error')
        def error():
            1 // 0
        c = app.test_client()
        rv = c.get('/')
        self.assert_equal(rv.status_code, 404)
        self.assert_equal(rv.data, b'not found')
        rv = c.get('/error')
        self.assert_equal(rv.status_code, 500)
        self.assert_equal(b'internal server error', rv.data)

    def test_before_request_and_routing_errors(self):
        app = flask.Flask(__name__)
        @app.before_request
        def attach_something():
            flask.g.something = 'value'
        @app.errorhandler(404)
        def return_something(error):
            return flask.g.something, 404
        rv = app.test_client().get('/')
        self.assert_equal(rv.status_code, 404)
        self.assert_equal(rv.data, b'value')

    def test_user_error_handling(self):
        class MyException(Exception):
            pass

        app = flask.Flask(__name__)
        @app.errorhandler(MyException)
        def handle_my_exception(e):
            self.assert_true(isinstance(e, MyException))
            return '42'
        @app.route('/')
        def index():
            raise MyException()

        c = app.test_client()
        self.assert_equal(c.get('/').data, b'42')

    def test_trapping_of_bad_request_key_errors(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/fail')
        def fail():
            flask.request.form['missing_key']
        c = app.test_client()
        self.assert_equal(c.get('/fail').status_code, 400)

        app.config['TRAP_BAD_REQUEST_ERRORS'] = True
        c = app.test_client()
        try:
            c.get('/fail')
        except KeyError as e:
            self.assert_true(isinstance(e, BadRequest))
        else:
            self.fail('Expected exception')

    def test_trapping_of_all_http_exceptions(self):
        app = flask.Flask(__name__)
        app.testing = True
        app.config['TRAP_HTTP_EXCEPTIONS'] = True
        @app.route('/fail')
        def fail():
            flask.abort(404)

        c = app.test_client()
        try:
            c.get('/fail')
        except NotFound as e:
            pass
        else:
            self.fail('Expected exception')

    def test_enctype_debug_helper(self):
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
            try:
                c.post('/fail', data={'foo': 'index.txt'})
            except DebugFilesKeyError as e:
                self.assert_in('no file contents were transmitted', str(e))
                self.assert_in('This was submitted: "index.txt"', str(e))
            else:
                self.fail('Expected exception')

    def test_response_creation(self):
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
        c = app.test_client()
        self.assert_equal(c.get('/unicode').data, u'Hällo Wörld'.encode('utf-8'))
        self.assert_equal(c.get('/string').data, u'Hällo Wörld'.encode('utf-8'))
        rv = c.get('/args')
        self.assert_equal(rv.data, b'Meh')
        self.assert_equal(rv.headers['X-Foo'], 'Testing')
        self.assert_equal(rv.status_code, 400)
        self.assert_equal(rv.mimetype, 'text/plain')

    def test_make_response(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.make_response()
            self.assert_equal(rv.status_code, 200)
            self.assert_equal(rv.data, b'')
            self.assert_equal(rv.mimetype, 'text/html')

            rv = flask.make_response('Awesome')
            self.assert_equal(rv.status_code, 200)
            self.assert_equal(rv.data, b'Awesome')
            self.assert_equal(rv.mimetype, 'text/html')

            rv = flask.make_response('W00t', 404)
            self.assert_equal(rv.status_code, 404)
            self.assert_equal(rv.data, b'W00t')
            self.assert_equal(rv.mimetype, 'text/html')

    def test_make_response_with_response_instance(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.make_response(
                flask.jsonify({'msg': 'W00t'}), 400)
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'{\n  "msg": "W00t"\n}')
            self.assertEqual(rv.mimetype, 'application/json')

            rv = flask.make_response(
                flask.Response(''), 400)
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.data, b'')
            self.assertEqual(rv.mimetype, 'text/html')

            rv = flask.make_response(
                flask.Response('', headers={'Content-Type': 'text/html'}),
                400, [('X-Foo', 'bar')])
            self.assertEqual(rv.status_code, 400)
            self.assertEqual(rv.headers['Content-Type'], 'text/html')
            self.assertEqual(rv.headers['X-Foo'], 'bar')

    def test_url_generation(self):
        app = flask.Flask(__name__)
        @app.route('/hello/<name>', methods=['POST'])
        def hello():
            pass
        with app.test_request_context():
            self.assert_equal(flask.url_for('hello', name='test x'), '/hello/test%20x')
            self.assert_equal(flask.url_for('hello', name='test x', _external=True),
                              'http://localhost/hello/test%20x')

    def test_build_error_handler(self):
        app = flask.Flask(__name__)

        # Test base case, a URL which results in a BuildError.
        with app.test_request_context():
            self.assertRaises(BuildError, flask.url_for, 'spam')

        # Verify the error is re-raised if not the current exception.
        try:
            with app.test_request_context():
                flask.url_for('spam')
        except BuildError as err:
            error = err
        try:
            raise RuntimeError('Test case where BuildError is not current.')
        except RuntimeError:
            self.assertRaises(BuildError, app.handle_url_build_error, error, 'spam', {})

        # Test a custom handler.
        def handler(error, endpoint, values):
            # Just a test.
            return '/test_handler/'
        app.url_build_error_handlers.append(handler)
        with app.test_request_context():
            self.assert_equal(flask.url_for('spam'), '/test_handler/')

    def test_custom_converters(self):
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
        self.assert_equal(c.get('/1,2,3').data, b'1|2|3')

    def test_static_files(self):
        app = flask.Flask(__name__)
        app.testing = True
        rv = app.test_client().get('/static/index.html')
        self.assert_equal(rv.status_code, 200)
        self.assert_equal(rv.data.strip(), b'<h1>Hello World!</h1>')
        with app.test_request_context():
            self.assert_equal(flask.url_for('static', filename='index.html'),
                              '/static/index.html')
        rv.close()

    def test_none_response(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def test():
            return None
        try:
            app.test_client().get('/')
        except ValueError as e:
            self.assert_equal(str(e), 'View function did not return a response')
            pass
        else:
            self.assert_true("Expected ValueError")

    def test_request_locals(self):
        self.assert_equal(repr(flask.g), '<LocalProxy unbound>')
        self.assertFalse(flask.g)

    def test_test_app_proper_environ(self):
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
        self.assert_equal(rv.data, b'Foo')

        rv = app.test_client().get('/', 'http://localhost.localdomain:5000')
        self.assert_equal(rv.data, b'Foo')

        rv = app.test_client().get('/', 'https://localhost.localdomain:5000')
        self.assert_equal(rv.data, b'Foo')

        app.config.update(SERVER_NAME='localhost.localdomain')
        rv = app.test_client().get('/', 'https://localhost.localdomain')
        self.assert_equal(rv.data, b'Foo')

        try:
            app.config.update(SERVER_NAME='localhost.localdomain:443')
            rv = app.test_client().get('/', 'https://localhost.localdomain')
            # Werkzeug 0.8
            self.assert_equal(rv.status_code, 404)
        except ValueError as e:
            # Werkzeug 0.7
            self.assert_equal(str(e), "the server name provided " +
                    "('localhost.localdomain:443') does not match the " + \
                    "server name from the WSGI environment ('localhost.localdomain')")

        try:
            app.config.update(SERVER_NAME='localhost.localdomain')
            rv = app.test_client().get('/', 'http://foo.localhost')
            # Werkzeug 0.8
            self.assert_equal(rv.status_code, 404)
        except ValueError as e:
            # Werkzeug 0.7
            self.assert_equal(str(e), "the server name provided " + \
                    "('localhost.localdomain') does not match the " + \
                    "server name from the WSGI environment ('foo.localhost')")

        rv = app.test_client().get('/', 'http://foo.localhost.localdomain')
        self.assert_equal(rv.data, b'Foo SubDomain')

    def test_exception_propagation(self):
        def apprunner(configkey):
            app = flask.Flask(__name__)
            @app.route('/')
            def index():
                1 // 0
            c = app.test_client()
            if config_key is not None:
                app.config[config_key] = True
                try:
                    resp = c.get('/')
                except Exception:
                    pass
                else:
                    self.fail('expected exception')
            else:
                self.assert_equal(c.get('/').status_code, 500)

        # we have to run this test in an isolated thread because if the
        # debug flag is set to true and an exception happens the context is
        # not torn down.  This causes other tests that run after this fail
        # when they expect no exception on the stack.
        for config_key in 'TESTING', 'PROPAGATE_EXCEPTIONS', 'DEBUG', None:
            t = Thread(target=apprunner, args=(config_key,))
            t.start()
            t.join()

    def test_max_content_length(self):
        app = flask.Flask(__name__)
        app.config['MAX_CONTENT_LENGTH'] = 64
        @app.before_request
        def always_first():
            flask.request.form['myfile']
            self.assert_true(False)
        @app.route('/accept', methods=['POST'])
        def accept_file():
            flask.request.form['myfile']
            self.assert_true(False)
        @app.errorhandler(413)
        def catcher(error):
            return '42'

        c = app.test_client()
        rv = c.post('/accept', data={'myfile': 'foo' * 100})
        self.assert_equal(rv.data, b'42')

    def test_url_processors(self):
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

        self.assert_equal(c.get('/de/').data, b'/de/about')
        self.assert_equal(c.get('/de/about').data, b'/foo')
        self.assert_equal(c.get('/foo').data, b'/en/about')

    def test_inject_blueprint_url_defaults(self):
        app = flask.Flask(__name__)
        bp = flask.Blueprint('foo.bar.baz', __name__,
                       template_folder='template')

        @bp.url_defaults
        def bp_defaults(endpoint, values):
            values['page'] = 'login'
        @bp.route('/<page>')
        def view(page): pass

        app.register_blueprint(bp)

        values = dict()
        app.inject_url_defaults('foo.bar.baz.view', values)
        expected = dict(page='login')
        self.assert_equal(values, expected)

        with app.test_request_context('/somepage'):
            url = flask.url_for('foo.bar.baz.view')
        expected = '/login'
        self.assert_equal(url, expected)

    def test_nonascii_pathinfo(self):
        app = flask.Flask(__name__)
        app.testing = True

        @app.route(u'/киртест')
        def index():
            return 'Hello World!'

        c = app.test_client()
        rv = c.get(u'/киртест')
        self.assert_equal(rv.data, b'Hello World!')

    def test_debug_mode_complains_after_first_request(self):
        app = flask.Flask(__name__)
        app.debug = True
        @app.route('/')
        def index():
            return 'Awesome'
        self.assert_false(app.got_first_request)
        self.assert_equal(app.test_client().get('/').data, b'Awesome')
        try:
            @app.route('/foo')
            def broken():
                return 'Meh'
        except AssertionError as e:
            self.assert_in('A setup function was called', str(e))
        else:
            self.fail('Expected exception')

        app.debug = False
        @app.route('/foo')
        def working():
            return 'Meh'
        self.assert_equal(app.test_client().get('/foo').data, b'Meh')
        self.assert_true(app.got_first_request)

    def test_before_first_request_functions(self):
        got = []
        app = flask.Flask(__name__)
        @app.before_first_request
        def foo():
            got.append(42)
        c = app.test_client()
        c.get('/')
        self.assert_equal(got, [42])
        c.get('/')
        self.assert_equal(got, [42])
        self.assert_true(app.got_first_request)

    def test_routing_redirect_debugging(self):
        app = flask.Flask(__name__)
        app.debug = True
        @app.route('/foo/', methods=['GET', 'POST'])
        def foo():
            return 'success'
        with app.test_client() as c:
            try:
                c.post('/foo', data={})
            except AssertionError as e:
                self.assert_in('http://localhost/foo/', str(e))
                self.assert_in('Make sure to directly send your POST-request '
                               'to this URL', str(e))
            else:
                self.fail('Expected exception')

            rv = c.get('/foo', data={}, follow_redirects=True)
            self.assert_equal(rv.data, b'success')

        app.debug = False
        with app.test_client() as c:
            rv = c.post('/foo', data={}, follow_redirects=True)
            self.assert_equal(rv.data, b'success')

    def test_route_decorator_custom_endpoint(self):
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
        self.assertEqual(c.get('/foo/').data, b'foo')
        self.assertEqual(c.get('/bar/').data, b'bar')
        self.assertEqual(c.get('/bar/123').data, b'123')

    def test_preserve_only_once(self):
        app = flask.Flask(__name__)
        app.debug = True

        @app.route('/fail')
        def fail_func():
            1 // 0

        c = app.test_client()
        for x in range(3):
            with self.assert_raises(ZeroDivisionError):
                c.get('/fail')

        self.assert_true(flask._request_ctx_stack.top is not None)
        self.assert_true(flask._app_ctx_stack.top is not None)
        # implicit appctx disappears too
        flask._request_ctx_stack.top.pop()
        self.assert_true(flask._request_ctx_stack.top is None)
        self.assert_true(flask._app_ctx_stack.top is None)

    def test_preserve_remembers_exception(self):
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
        with self.assert_raises(ZeroDivisionError):
            c.get('/fail')
        self.assert_equal(errors, [])

        # But this request triggers it, and it's an error
        c.get('/success')
        self.assert_equal(len(errors), 2)
        self.assert_true(isinstance(errors[0], ZeroDivisionError))

        # At this point another request does nothing.
        c.get('/success')
        self.assert_equal(len(errors), 3)
        self.assert_equal(errors[1], None)

    def test_get_method_on_g(self):
        app = flask.Flask(__name__)
        app.testing = True

        with app.app_context():
            self.assert_equal(flask.g.get('x'), None)
            self.assert_equal(flask.g.get('x', 11), 11)
            flask.g.x = 42
            self.assert_equal(flask.g.get('x'), 42)
            self.assert_equal(flask.g.x, 42)

    def test_g_iteration_protocol(self):
        app = flask.Flask(__name__)
        app.testing = True

        with app.app_context():
            flask.g.foo = 23
            flask.g.bar = 42
            self.assert_equal('foo' in flask.g, True)
            self.assert_equal('foos' in flask.g, False)
            self.assert_equal(sorted(flask.g), ['bar', 'foo'])


class SubdomainTestCase(FlaskTestCase):

    def test_basic_support(self):
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
        self.assert_equal(rv.data, b'normal index')

        rv = c.get('/', 'http://test.localhost/')
        self.assert_equal(rv.data, b'test index')

    @emits_module_deprecation_warning
    def test_module_static_path_subdomain(self):
        app = flask.Flask(__name__)
        app.config['SERVER_NAME'] = 'example.com'
        from subdomaintestmodule import mod
        app.register_module(mod)
        c = app.test_client()
        rv = c.get('/static/hello.txt', 'http://foo.example.com/')
        rv.direct_passthrough = False
        self.assert_equal(rv.data.strip(), b'Hello Subdomain')
        rv.close()

    def test_subdomain_matching(self):
        app = flask.Flask(__name__)
        app.config['SERVER_NAME'] = 'localhost'
        @app.route('/', subdomain='<user>')
        def index(user):
            return 'index for %s' % user

        c = app.test_client()
        rv = c.get('/', 'http://mitsuhiko.localhost/')
        self.assert_equal(rv.data, b'index for mitsuhiko')

    def test_subdomain_matching_with_ports(self):
        app = flask.Flask(__name__)
        app.config['SERVER_NAME'] = 'localhost:3000'
        @app.route('/', subdomain='<user>')
        def index(user):
            return 'index for %s' % user

        c = app.test_client()
        rv = c.get('/', 'http://mitsuhiko.localhost:3000/')
        self.assert_equal(rv.data, b'index for mitsuhiko')

    @emits_module_deprecation_warning
    def test_module_subdomain_support(self):
        app = flask.Flask(__name__)
        mod = flask.Module(__name__, 'test', subdomain='testing')
        app.config['SERVER_NAME'] = 'localhost'

        @mod.route('/test')
        def test():
            return 'Test'

        @mod.route('/outside', subdomain='xtesting')
        def bar():
            return 'Outside'

        app.register_module(mod)

        c = app.test_client()
        rv = c.get('/test', 'http://testing.localhost/')
        self.assert_equal(rv.data, b'Test')
        rv = c.get('/outside', 'http://xtesting.localhost/')
        self.assert_equal(rv.data, b'Outside')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BasicFunctionalityTestCase))
    suite.addTest(unittest.makeSuite(SubdomainTestCase))
    return suite
