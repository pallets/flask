# -*- coding: utf-8 -*-
"""
    Flask Tests
    ~~~~~~~~~~~

    Tests Flask itself.  The majority of Flask is already tested
    as part of Werkzeug.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import os
import re
import sys
import flask
import flask.views
import unittest
import warnings
from threading import Thread
from logging import StreamHandler
from contextlib import contextmanager
from functools import update_wrapper
from datetime import datetime
from werkzeug import parse_date, parse_options_header
from werkzeug.exceptions import NotFound, BadRequest
from werkzeug.http import parse_set_header
from jinja2 import TemplateNotFound
from cStringIO import StringIO

example_path = os.path.join(os.path.dirname(__file__), '..', 'examples')
sys.path.append(os.path.join(example_path, 'flaskr'))
sys.path.append(os.path.join(example_path, 'minitwit'))


def has_encoding(name):
    try:
        import codecs
        codecs.lookup(name)
        return True
    except LookupError:
        return False


# config keys used for the ConfigTestCase
TEST_KEY = 'foo'
SECRET_KEY = 'devkey'


# import moduleapp here because it uses deprecated features and we don't
# want to see the warnings
warnings.simplefilter('ignore', DeprecationWarning)
from moduleapp import app as moduleapp
warnings.simplefilter('default', DeprecationWarning)


@contextmanager
def catch_warnings():
    """Catch warnings in a with block in a list"""
    # make sure deprecation warnings are active in tests
    warnings.simplefilter('default', category=DeprecationWarning)

    filters = warnings.filters
    warnings.filters = filters[:]
    old_showwarning = warnings.showwarning
    log = []
    def showwarning(message, category, filename, lineno, file=None, line=None):
        log.append(locals())
    try:
        warnings.showwarning = showwarning
        yield log
    finally:
        warnings.filters = filters
        warnings.showwarning = old_showwarning


@contextmanager
def catch_stderr():
    """Catch stderr in a StringIO"""
    old_stderr = sys.stderr
    sys.stderr = rv = StringIO()
    try:
        yield rv
    finally:
        sys.stderr = old_stderr


def emits_module_deprecation_warning(f):
    def new_f(*args, **kwargs):
        with catch_warnings() as log:
            f(*args, **kwargs)
            assert log, 'expected deprecation warning'
            for entry in log:
                assert 'Modules are deprecated' in str(entry['message'])
    return update_wrapper(new_f, f)


class ContextTestCase(unittest.TestCase):

    def test_context_binding(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return 'Hello %s!' % flask.request.args['name']
        @app.route('/meh')
        def meh():
            return flask.request.url

        with app.test_request_context('/?name=World'):
            assert index() == 'Hello World!'
        with app.test_request_context('/meh'):
            assert meh() == 'http://localhost/meh'
        assert flask._request_ctx_stack.top is None

    def test_context_test(self):
        app = flask.Flask(__name__)
        assert not flask.request
        assert not flask.has_request_context()
        ctx = app.test_request_context()
        ctx.push()
        try:
            assert flask.request
            assert flask.has_request_context()
        finally:
            ctx.pop()

    def test_manual_context_binding(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return 'Hello %s!' % flask.request.args['name']

        ctx = app.test_request_context('/?name=World')
        ctx.push()
        assert index() == 'Hello World!'
        ctx.pop()
        try:
            index()
        except RuntimeError:
            pass
        else:
            assert 0, 'expected runtime error'

    def test_test_client_context_binding(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            flask.g.value = 42
            return 'Hello World!'

        @app.route('/other')
        def other():
            1/0

        with app.test_client() as c:
            resp = c.get('/')
            assert flask.g.value == 42
            assert resp.data == 'Hello World!'
            assert resp.status_code == 200

            resp = c.get('/other')
            assert not hasattr(flask.g, 'value')
            assert 'Internal Server Error' in resp.data
            assert resp.status_code == 500
            flask.g.value = 23

        try:
            flask.g.value
        except (AttributeError, RuntimeError):
            pass
        else:
            raise AssertionError('some kind of exception expected')


class BasicFunctionalityTestCase(unittest.TestCase):

    def test_options_work(self):
        app = flask.Flask(__name__)
        @app.route('/', methods=['GET', 'POST'])
        def index():
            return 'Hello World'
        rv = app.test_client().open('/', method='OPTIONS')
        assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST']
        assert rv.data == ''

    def test_options_on_multiple_rules(self):
        app = flask.Flask(__name__)
        @app.route('/', methods=['GET', 'POST'])
        def index():
            return 'Hello World'
        @app.route('/', methods=['PUT'])
        def index_put():
            return 'Aha!'
        rv = app.test_client().open('/', method='OPTIONS')
        assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST', 'PUT']

    def test_options_handling_disabled(self):
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

    def test_request_dispatching(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.request.method
        @app.route('/more', methods=['GET', 'POST'])
        def more():
            return flask.request.method

        c = app.test_client()
        assert c.get('/').data == 'GET'
        rv = c.post('/')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS']
        rv = c.head('/')
        assert rv.status_code == 200
        assert not rv.data  # head truncates
        assert c.post('/more').data == 'POST'
        assert c.get('/more').data == 'GET'
        rv = c.delete('/more')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST']

    def test_url_mapping(self):
        app = flask.Flask(__name__)
        def index():
            return flask.request.method
        def more():
            return flask.request.method

        app.add_url_rule('/', 'index', index)
        app.add_url_rule('/more', 'more', more, methods=['GET', 'POST'])

        c = app.test_client()
        assert c.get('/').data == 'GET'
        rv = c.post('/')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS']
        rv = c.head('/')
        assert rv.status_code == 200
        assert not rv.data  # head truncates
        assert c.post('/more').data == 'POST'
        assert c.get('/more').data == 'GET'
        rv = c.delete('/more')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'OPTIONS', 'POST']

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
        assert c.get('/foo/').data == 'index'
        assert c.get('/foo/bar').data == 'bar'

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
        assert c.get('/foo/').data == 'index'
        assert c.get('/foo/bar').data == 'bar'

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
        assert c.post('/set', data={'value': '42'}).data == 'value set'
        assert c.get('/get').data == '42'

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
        assert 'domain=.example.com' in rv.headers['set-cookie'].lower()
        assert 'httponly' in rv.headers['set-cookie'].lower()

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
        assert 'domain=.example.com' in rv.headers['set-cookie'].lower()
        assert 'httponly' in rv.headers['set-cookie'].lower()

    def test_missing_session(self):
        app = flask.Flask(__name__)
        def expect_exception(f, *args, **kwargs):
            try:
                f(*args, **kwargs)
            except RuntimeError, e:
                assert e.args and 'session is unavailable' in e.args[0]
            else:
                assert False, 'expected exception'
        with app.test_request_context():
            assert flask.session.get('missing_key') is None
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
            return unicode(flask.session.permanent)

        client = app.test_client()
        rv = client.get('/')
        assert 'set-cookie' in rv.headers
        match = re.search(r'\bexpires=([^;]+)', rv.headers['set-cookie'])
        expires = parse_date(match.group())
        expected = datetime.utcnow() + app.permanent_session_lifetime
        assert expires.year == expected.year
        assert expires.month == expected.month
        assert expires.day == expected.day

        rv = client.get('/test')
        assert rv.data == 'True'

        permanent = False
        rv = app.test_client().get('/')
        assert 'set-cookie' in rv.headers
        match = re.search(r'\bexpires=([^;]+)', rv.headers['set-cookie'])
        assert match is None

    def test_flashes(self):
        app = flask.Flask(__name__)
        app.secret_key = 'testkey'

        with app.test_request_context():
            assert not flask.session.modified
            flask.flash('Zap')
            flask.session.modified = False
            flask.flash('Zip')
            assert flask.session.modified
            assert list(flask.get_flashed_messages()) == ['Zap', 'Zip']

    def test_extended_flashing(self):
        app = flask.Flask(__name__)
        app.secret_key = 'testkey'

        @app.route('/')
        def index():
            flask.flash(u'Hello World')
            flask.flash(u'Hello World', 'error')
            flask.flash(flask.Markup(u'<em>Testing</em>'), 'warning')
            return ''

        @app.route('/test')
        def test():
            messages = flask.get_flashed_messages(with_categories=True)
            assert len(messages) == 3
            assert messages[0] == ('message', u'Hello World')
            assert messages[1] == ('error', u'Hello World')
            assert messages[2] == ('warning', flask.Markup(u'<em>Testing</em>'))
            return ''
            messages = flask.get_flashed_messages()
            assert len(messages) == 3
            assert messages[0] == u'Hello World'
            assert messages[1] == u'Hello World'
            assert messages[2] == flask.Markup(u'<em>Testing</em>')

        c = app.test_client()
        c.get('/')
        c.get('/test')

    def test_request_processing(self):
        app = flask.Flask(__name__)
        evts = []
        @app.before_request
        def before_request():
            evts.append('before')
        @app.after_request
        def after_request(response):
            response.data += '|after'
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
        assert rv == 'request|after'

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
        assert rv.status_code == 200
        assert 'Response' in rv.data
        assert len(called) == 1

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
        assert rv.status_code == 200
        assert 'Response' in rv.data
        assert len(called) == 1

    def test_teardown_request_handler_error(self):
        called = []
        app = flask.Flask(__name__)
        @app.teardown_request
        def teardown_request1(exc):
            assert type(exc) == ZeroDivisionError
            called.append(True)
            # This raises a new error and blows away sys.exc_info(), so we can
            # test that all teardown_requests get passed the same original
            # exception.
            try:
                raise TypeError
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
                raise TypeError
            except:
                pass
        @app.route('/')
        def fails():
            1/0
        rv = app.test_client().get('/')
        assert rv.status_code == 500
        assert 'Internal Server Error' in rv.data
        assert len(called) == 2

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
        assert rv.data == '42'
        assert called == [1, 2, 3, 4, 5, 6]

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
        assert rv.status_code == 404
        assert rv.data == 'not found'
        rv = c.get('/error')
        assert rv.status_code == 500
        assert 'internal server error' == rv.data

    def test_before_request_and_routing_errors(self):
        app = flask.Flask(__name__)
        @app.before_request
        def attach_something():
            flask.g.something = 'value'
        @app.errorhandler(404)
        def return_something(error):
            return flask.g.something, 404
        rv = app.test_client().get('/')
        assert rv.status_code == 404
        assert rv.data == 'value'

    def test_user_error_handling(self):
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
        assert c.get('/').data == '42'

    def test_trapping_of_bad_request_key_errors(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/fail')
        def fail():
            flask.request.form['missing_key']
        c = app.test_client()
        assert c.get('/fail').status_code == 400

        app.config['TRAP_BAD_REQUEST_ERRORS'] = True
        c = app.test_client()
        try:
            c.get('/fail')
        except KeyError, e:
            assert isinstance(e, BadRequest)
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
        except NotFound, e:
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
            except DebugFilesKeyError, e:
                assert 'no file contents were transmitted' in str(e)
                assert 'This was submitted: "index.txt"' in str(e)
            else:
                self.fail('Expected exception')

    def test_teardown_on_pop(self):
        buffer = []
        app = flask.Flask(__name__)
        @app.teardown_request
        def end_of_request(exception):
            buffer.append(exception)

        ctx = app.test_request_context()
        ctx.push()
        assert buffer == []
        ctx.pop()
        assert buffer == [None]

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
            return 'Meh', 400, {'X-Foo': 'Testing'}, 'text/plain'
        c = app.test_client()
        assert c.get('/unicode').data == u'Hällo Wörld'.encode('utf-8')
        assert c.get('/string').data == u'Hällo Wörld'.encode('utf-8')
        rv = c.get('/args')
        assert rv.data == 'Meh'
        assert rv.headers['X-Foo'] == 'Testing'
        assert rv.status_code == 400
        assert rv.mimetype == 'text/plain'

    def test_make_response(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.make_response()
            assert rv.status_code == 200
            assert rv.data == ''
            assert rv.mimetype == 'text/html'

            rv = flask.make_response('Awesome')
            assert rv.status_code == 200
            assert rv.data == 'Awesome'
            assert rv.mimetype == 'text/html'

            rv = flask.make_response('W00t', 404)
            assert rv.status_code == 404
            assert rv.data == 'W00t'
            assert rv.mimetype == 'text/html'

    def test_url_generation(self):
        app = flask.Flask(__name__)
        @app.route('/hello/<name>', methods=['POST'])
        def hello():
            pass
        with app.test_request_context():
            assert flask.url_for('hello', name='test x') == '/hello/test%20x'
            assert flask.url_for('hello', name='test x', _external=True) \
                == 'http://localhost/hello/test%20x'

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
        assert c.get('/1,2,3').data == '1|2|3'

    def test_static_files(self):
        app = flask.Flask(__name__)
        rv = app.test_client().get('/static/index.html')
        assert rv.status_code == 200
        assert rv.data.strip() == '<h1>Hello World!</h1>'
        with app.test_request_context():
            assert flask.url_for('static', filename='index.html') \
                == '/static/index.html'

    def test_none_response(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def test():
            return None
        try:
            app.test_client().get('/')
        except ValueError, e:
            assert str(e) == 'View function did not return a response'
            pass
        else:
            assert "Expected ValueError"

    def test_request_locals(self):
        self.assertEqual(repr(flask.g), '<LocalProxy unbound>')
        self.assertFalse(flask.g)

    def test_proper_test_request_context(self):
        app = flask.Flask(__name__)
        app.config.update(
            SERVER_NAME='localhost.localdomain:5000'
        )

        @app.route('/')
        def index():
            return None

        @app.route('/', subdomain='foo')
        def sub():
            return None

        with app.test_request_context('/'):
            assert flask.url_for('index', _external=True) == 'http://localhost.localdomain:5000/'

        with app.test_request_context('/'):
            assert flask.url_for('sub', _external=True) == 'http://foo.localhost.localdomain:5000/'

        try:
            with app.test_request_context('/', environ_overrides={'HTTP_HOST': 'localhost'}):
                pass
        except Exception, e:
            assert isinstance(e, ValueError)
            assert str(e) == "the server name provided " + \
                    "('localhost.localdomain:5000') does not match the " + \
                    "server name from the WSGI environment ('localhost')", str(e)

        try:
            app.config.update(SERVER_NAME='localhost')
            with app.test_request_context('/', environ_overrides={'SERVER_NAME': 'localhost'}):
                pass
        except ValueError, e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

        try:
            app.config.update(SERVER_NAME='localhost:80')
            with app.test_request_context('/', environ_overrides={'SERVER_NAME': 'localhost:80'}):
                pass
        except ValueError, e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

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

        try:
            rv = app.test_client().get('/')
            assert rv.data == 'Foo'
        except ValueError, e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

        try:
            rv = app.test_client().get('/', 'http://localhost.localdomain:5000')
            assert rv.data == 'Foo'
        except ValueError, e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

        try:
            rv = app.test_client().get('/', 'https://localhost.localdomain:5000')
            assert rv.data == 'Foo'
        except ValueError, e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

        try:
            app.config.update(SERVER_NAME='localhost.localdomain')
            rv = app.test_client().get('/', 'https://localhost.localdomain')
            assert rv.data == 'Foo'
        except ValueError, e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

        try:
            app.config.update(SERVER_NAME='localhost.localdomain:443')
            rv = app.test_client().get('/', 'https://localhost.localdomain')
            assert rv.data == 'Foo'
        except ValueError, e:
            assert str(e) == "the server name provided " + \
                    "('localhost.localdomain:443') does not match the " + \
                    "server name from the WSGI environment ('localhost.localdomain')", str(e)

        try:
            app.config.update(SERVER_NAME='localhost.localdomain')
            app.test_client().get('/', 'http://foo.localhost')
        except ValueError, e:
            assert str(e) == "the server name provided " + \
                    "('localhost.localdomain') does not match the " + \
                    "server name from the WSGI environment ('foo.localhost')", str(e)

        try:
            rv = app.test_client().get('/', 'http://foo.localhost.localdomain')
            assert rv.data == 'Foo SubDomain'
        except ValueError, e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

    def test_exception_propagation(self):
        def apprunner(configkey):
            app = flask.Flask(__name__)
            @app.route('/')
            def index():
                1/0
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
                assert c.get('/').status_code == 500

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
        assert rv.data == '42'

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

        self.assertEqual(c.get('/de/').data, '/de/about')
        self.assertEqual(c.get('/de/about').data, '/foo')
        self.assertEqual(c.get('/foo').data, '/en/about')

    def test_debug_mode_complains_after_first_request(self):
        app = flask.Flask(__name__)
        app.debug = True
        @app.route('/')
        def index():
            return 'Awesome'
        self.assert_(not app.got_first_request)
        self.assertEqual(app.test_client().get('/').data, 'Awesome')
        try:
            @app.route('/foo')
            def broken():
                return 'Meh'
        except AssertionError, e:
            self.assert_('A setup function was called' in str(e))
        else:
            self.fail('Expected exception')

        app.debug = False
        @app.route('/foo')
        def working():
            return 'Meh'
        self.assertEqual(app.test_client().get('/foo').data, 'Meh')
        self.assert_(app.got_first_request)

    def test_before_first_request_functions(self):
        got = []
        app = flask.Flask(__name__)
        @app.before_first_request
        def foo():
            got.append(42)
        c = app.test_client()
        c.get('/')
        self.assertEqual(got, [42])
        c.get('/')
        self.assertEqual(got, [42])
        self.assert_(app.got_first_request)

    def test_routing_redirect_debugging(self):
        app = flask.Flask(__name__)
        app.debug = True
        @app.route('/foo/', methods=['GET', 'POST'])
        def foo():
            return 'success'
        with app.test_client() as c:
            try:
                c.post('/foo', data={})
            except AssertionError, e:
                self.assert_('http://localhost/foo/' in str(e))
                self.assert_('Make sure to directly send your POST-request '
                             'to this URL' in str(e))
            else:
                self.fail('Expected exception')

            rv = c.get('/foo', data={}, follow_redirects=True)
            self.assertEqual(rv.data, 'success')

        app.debug = False
        with app.test_client() as c:
            rv = c.post('/foo', data={}, follow_redirects=True)
            self.assertEqual(rv.data, 'success')


class InstanceTestCase(unittest.TestCase):

    def test_explicit_instance_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        try:
            flask.Flask(__name__, instance_path='instance')
        except ValueError, e:
            self.assert_('must be absolute' in str(e))
        else:
            self.fail('Expected value error')

        app = flask.Flask(__name__, instance_path=here)
        self.assertEqual(app.instance_path, here)

    def test_uninstalled_module_paths(self):
        here = os.path.abspath(os.path.dirname(__file__))
        app = flask.Flask(__name__)
        self.assertEqual(app.instance_path, os.path.join(here, 'instance'))

    def test_uninstalled_package_paths(self):
        from blueprintapp import app
        here = os.path.abspath(os.path.dirname(__file__))
        self.assertEqual(app.instance_path, os.path.join(here, 'instance'))

    def test_installed_module_paths(self):
        import types
        expected_prefix = os.path.abspath('foo')
        mod = types.ModuleType('myapp')
        mod.__file__ = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'myapp.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assertEqual(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None

    def test_installed_package_paths(self):
        import types
        expected_prefix = os.path.abspath('foo')
        package_path = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'myapp')
        mod = types.ModuleType('myapp')
        mod.__path__ = [package_path]
        mod.__file__ = os.path.join(package_path, '__init__.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assertEqual(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None

    def test_prefix_installed_paths(self):
        import types
        expected_prefix = os.path.abspath(sys.prefix)
        package_path = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'myapp')
        mod = types.ModuleType('myapp')
        mod.__path__ = [package_path]
        mod.__file__ = os.path.join(package_path, '__init__.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assertEqual(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None

    def test_egg_installed_paths(self):
        import types
        expected_prefix = os.path.abspath(sys.prefix)
        package_path = os.path.join(expected_prefix, 'lib', 'python2.5',
                                    'site-packages', 'MyApp.egg', 'myapp')
        mod = types.ModuleType('myapp')
        mod.__path__ = [package_path]
        mod.__file__ = os.path.join(package_path, '__init__.py')
        sys.modules['myapp'] = mod
        try:
            mod.app = flask.Flask(mod.__name__)
            self.assertEqual(mod.app.instance_path,
                             os.path.join(expected_prefix, 'var',
                                          'myapp-instance'))
        finally:
            sys.modules['myapp'] = None


class JSONTestCase(unittest.TestCase):

    def test_json_bad_requests(self):
        app = flask.Flask(__name__)
        @app.route('/json', methods=['POST'])
        def return_json():
            return unicode(flask.request.json)
        c = app.test_client()
        rv = c.post('/json', data='malformed', content_type='application/json')
        self.assertEqual(rv.status_code, 400)

    def test_json_body_encoding(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            return flask.request.json

        c = app.test_client()
        resp = c.get('/', data=u'"Hällo Wörld"'.encode('iso-8859-15'),
                     content_type='application/json; charset=iso-8859-15')
        assert resp.data == u'Hällo Wörld'.encode('utf-8')

    def test_jsonify(self):
        d = dict(a=23, b=42, c=[1, 2, 3])
        app = flask.Flask(__name__)
        @app.route('/kw')
        def return_kwargs():
            return flask.jsonify(**d)
        @app.route('/dict')
        def return_dict():
            return flask.jsonify(d)
        c = app.test_client()
        for url in '/kw', '/dict':
            rv = c.get(url)
            assert rv.mimetype == 'application/json'
            assert flask.json.loads(rv.data) == d

    def test_json_attr(self):
        app = flask.Flask(__name__)
        @app.route('/add', methods=['POST'])
        def add():
            return unicode(flask.request.json['a'] + flask.request.json['b'])
        c = app.test_client()
        rv = c.post('/add', data=flask.json.dumps({'a': 1, 'b': 2}),
                            content_type='application/json')
        assert rv.data == '3'

    def test_template_escaping(self):
        app = flask.Flask(__name__)
        render = flask.render_template_string
        with app.test_request_context():
            rv = render('{{ "</script>"|tojson|safe }}')
            assert rv == '"<\\/script>"'
            rv = render('{{ "<\0/script>"|tojson|safe }}')
            assert rv == '"<\\u0000\\/script>"'

    def test_modified_url_encoding(self):
        class ModifiedRequest(flask.Request):
            url_charset = 'euc-kr'
        app = flask.Flask(__name__)
        app.request_class = ModifiedRequest
        app.url_map.charset = 'euc-kr'

        @app.route('/')
        def index():
            return flask.request.args['foo']

        rv = app.test_client().get(u'/?foo=정상처리'.encode('euc-kr'))
        assert rv.status_code == 200
        assert rv.data == u'정상처리'.encode('utf-8')

    if not has_encoding('euc-kr'):
        test_modified_url_encoding = None


class TemplatingTestCase(unittest.TestCase):

    def test_context_processing(self):
        app = flask.Flask(__name__)
        @app.context_processor
        def context_processor():
            return {'injected_value': 42}
        @app.route('/')
        def index():
            return flask.render_template('context_template.html', value=23)
        rv = app.test_client().get('/')
        assert rv.data == '<p>23|42'

    def test_original_win(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.render_template_string('{{ config }}', config=42)
        rv = app.test_client().get('/')
        assert rv.data == '42'

    def test_standard_context(self):
        app = flask.Flask(__name__)
        app.secret_key = 'development key'
        @app.route('/')
        def index():
            flask.g.foo = 23
            flask.session['test'] = 'aha'
            return flask.render_template_string('''
                {{ request.args.foo }}
                {{ g.foo }}
                {{ config.DEBUG }}
                {{ session.test }}
            ''')
        rv = app.test_client().get('/?foo=42')
        assert rv.data.split() == ['42', '23', 'False', 'aha']

    def test_escaping(self):
        text = '<p>Hello World!'
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.render_template('escaping_template.html', text=text,
                                         html=flask.Markup(text))
        lines = app.test_client().get('/').data.splitlines()
        assert lines == [
            '&lt;p&gt;Hello World!',
            '<p>Hello World!',
            '<p>Hello World!',
            '<p>Hello World!',
            '&lt;p&gt;Hello World!',
            '<p>Hello World!'
        ]

    def test_no_escaping(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            assert flask.render_template_string('{{ foo }}',
                foo='<test>') == '<test>'
            assert flask.render_template('mail.txt', foo='<test>') \
                == '<test> Mail'

    def test_macros(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            macro = flask.get_template_attribute('_macro.html', 'hello')
            assert macro('World') == 'Hello World!'

    def test_template_filter(self):
        app = flask.Flask(__name__)
        @app.template_filter()
        def my_reverse(s):
            return s[::-1]
        assert 'my_reverse' in  app.jinja_env.filters.keys()
        assert app.jinja_env.filters['my_reverse'] == my_reverse
        assert app.jinja_env.filters['my_reverse']('abcd') == 'dcba'

    def test_template_filter_with_name(self):
        app = flask.Flask(__name__)
        @app.template_filter('strrev')
        def my_reverse(s):
            return s[::-1]
        assert 'strrev' in  app.jinja_env.filters.keys()
        assert app.jinja_env.filters['strrev'] == my_reverse
        assert app.jinja_env.filters['strrev']('abcd') == 'dcba'

    def test_template_filter_with_template(self):
        app = flask.Flask(__name__)
        @app.template_filter()
        def super_reverse(s):
            return s[::-1]
        @app.route('/')
        def index():
            return flask.render_template('template_filter.html', value='abcd')
        rv = app.test_client().get('/')
        assert rv.data == 'dcba'

    def test_template_filter_with_name_and_template(self):
        app = flask.Flask(__name__)
        @app.template_filter('super_reverse')
        def my_reverse(s):
            return s[::-1]
        @app.route('/')
        def index():
            return flask.render_template('template_filter.html', value='abcd')
        rv = app.test_client().get('/')
        assert rv.data == 'dcba'

    def test_custom_template_loader(self):
        class MyFlask(flask.Flask):
            def create_global_jinja_loader(self):
                from jinja2 import DictLoader
                return DictLoader({'index.html': 'Hello Custom World!'})
        app = MyFlask(__name__)
        @app.route('/')
        def index():
            return flask.render_template('index.html')
        c = app.test_client()
        rv = c.get('/')
        assert rv.data == 'Hello Custom World!'


class ModuleTestCase(unittest.TestCase):

    @emits_module_deprecation_warning
    def test_basic_module(self):
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin', url_prefix='/admin')
        @admin.route('/')
        def admin_index():
            return 'admin index'
        @admin.route('/login')
        def admin_login():
            return 'admin login'
        @admin.route('/logout')
        def admin_logout():
            return 'admin logout'
        @app.route('/')
        def index():
            return 'the index'
        app.register_module(admin)
        c = app.test_client()
        assert c.get('/').data == 'the index'
        assert c.get('/admin/').data == 'admin index'
        assert c.get('/admin/login').data == 'admin login'
        assert c.get('/admin/logout').data == 'admin logout'

    @emits_module_deprecation_warning
    def test_default_endpoint_name(self):
        app = flask.Flask(__name__)
        mod = flask.Module(__name__, 'frontend')
        def index():
            return 'Awesome'
        mod.add_url_rule('/', view_func=index)
        app.register_module(mod)
        rv = app.test_client().get('/')
        assert rv.data == 'Awesome'
        with app.test_request_context():
            assert flask.url_for('frontend.index') == '/'

    @emits_module_deprecation_warning
    def test_request_processing(self):
        catched = []
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin', url_prefix='/admin')
        @admin.before_request
        def before_admin_request():
            catched.append('before-admin')
        @admin.after_request
        def after_admin_request(response):
            catched.append('after-admin')
            return response
        @admin.route('/')
        def admin_index():
            return 'the admin'
        @app.before_request
        def before_request():
            catched.append('before-app')
        @app.after_request
        def after_request(response):
            catched.append('after-app')
            return response
        @app.route('/')
        def index():
            return 'the index'
        app.register_module(admin)
        c = app.test_client()

        assert c.get('/').data == 'the index'
        assert catched == ['before-app', 'after-app']
        del catched[:]

        assert c.get('/admin/').data == 'the admin'
        assert catched == ['before-app', 'before-admin',
                           'after-admin', 'after-app']

    @emits_module_deprecation_warning
    def test_context_processors(self):
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin', url_prefix='/admin')
        @app.context_processor
        def inject_all_regualr():
            return {'a': 1}
        @admin.context_processor
        def inject_admin():
            return {'b': 2}
        @admin.app_context_processor
        def inject_all_module():
            return {'c': 3}
        @app.route('/')
        def index():
            return flask.render_template_string('{{ a }}{{ b }}{{ c }}')
        @admin.route('/')
        def admin_index():
            return flask.render_template_string('{{ a }}{{ b }}{{ c }}')
        app.register_module(admin)
        c = app.test_client()
        assert c.get('/').data == '13'
        assert c.get('/admin/').data == '123'

    @emits_module_deprecation_warning
    def test_late_binding(self):
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin')
        @admin.route('/')
        def index():
            return '42'
        app.register_module(admin, url_prefix='/admin')
        assert app.test_client().get('/admin/').data == '42'

    @emits_module_deprecation_warning
    def test_error_handling(self):
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin')
        @admin.app_errorhandler(404)
        def not_found(e):
            return 'not found', 404
        @admin.app_errorhandler(500)
        def internal_server_error(e):
            return 'internal server error', 500
        @admin.route('/')
        def index():
            flask.abort(404)
        @admin.route('/error')
        def error():
            1 // 0
        app.register_module(admin)
        c = app.test_client()
        rv = c.get('/')
        assert rv.status_code == 404
        assert rv.data == 'not found'
        rv = c.get('/error')
        assert rv.status_code == 500
        assert 'internal server error' == rv.data

    def test_templates_and_static(self):
        app = moduleapp
        app.testing = True
        c = app.test_client()

        rv = c.get('/')
        assert rv.data == 'Hello from the Frontend'
        rv = c.get('/admin/')
        assert rv.data == 'Hello from the Admin'
        rv = c.get('/admin/index2')
        assert rv.data == 'Hello from the Admin'
        rv = c.get('/admin/static/test.txt')
        assert rv.data.strip() == 'Admin File'
        rv = c.get('/admin/static/css/test.css')
        assert rv.data.strip() == '/* nested file */'

        with app.test_request_context():
            assert flask.url_for('admin.static', filename='test.txt') \
                == '/admin/static/test.txt'

        with app.test_request_context():
            try:
                flask.render_template('missing.html')
            except TemplateNotFound, e:
                assert e.name == 'missing.html'
            else:
                assert 0, 'expected exception'

        with flask.Flask(__name__).test_request_context():
            assert flask.render_template('nested/nested.txt') == 'I\'m nested'

    def test_safe_access(self):
        app = moduleapp

        with app.test_request_context():
            f = app.view_functions['admin.static']

            try:
                f('/etc/passwd')
            except NotFound:
                pass
            else:
                assert 0, 'expected exception'
            try:
                f('../__init__.py')
            except NotFound:
                pass
            else:
                assert 0, 'expected exception'

            # testcase for a security issue that may exist on windows systems
            import os
            import ntpath
            old_path = os.path
            os.path = ntpath
            try:
                try:
                    f('..\\__init__.py')
                except NotFound:
                    pass
                else:
                    assert 0, 'expected exception'
            finally:
                os.path = old_path

    @emits_module_deprecation_warning
    def test_endpoint_decorator(self):
        from werkzeug.routing import Submount, Rule
        from flask import Module

        app = flask.Flask(__name__)
        app.testing = True
        app.url_map.add(Submount('/foo', [
            Rule('/bar', endpoint='bar'),
            Rule('/', endpoint='index')
        ]))
        module = Module(__name__, __name__)

        @module.endpoint('bar')
        def bar():
            return 'bar'

        @module.endpoint('index')
        def index():
            return 'index'

        app.register_module(module)

        c = app.test_client()
        assert c.get('/foo/').data == 'index'
        assert c.get('/foo/bar').data == 'bar'


class BlueprintTestCase(unittest.TestCase):

    def test_blueprint_specific_error_handling(self):
        frontend = flask.Blueprint('frontend', __name__)
        backend = flask.Blueprint('backend', __name__)
        sideend = flask.Blueprint('sideend', __name__)

        @frontend.errorhandler(403)
        def frontend_forbidden(e):
            return 'frontend says no', 403

        @frontend.route('/frontend-no')
        def frontend_no():
            flask.abort(403)

        @backend.errorhandler(403)
        def backend_forbidden(e):
            return 'backend says no', 403

        @backend.route('/backend-no')
        def backend_no():
            flask.abort(403)

        @sideend.route('/what-is-a-sideend')
        def sideend_no():
            flask.abort(403)

        app = flask.Flask(__name__)
        app.register_blueprint(frontend)
        app.register_blueprint(backend)
        app.register_blueprint(sideend)

        @app.errorhandler(403)
        def app_forbidden(e):
            return 'application itself says no', 403

        c = app.test_client()

        assert c.get('/frontend-no').data == 'frontend says no'
        assert c.get('/backend-no').data == 'backend says no'
        assert c.get('/what-is-a-sideend').data == 'application itself says no'

    def test_blueprint_url_definitions(self):
        bp = flask.Blueprint('test', __name__)

        @bp.route('/foo', defaults={'baz': 42})
        def foo(bar, baz):
            return '%s/%d' % (bar, baz)

        @bp.route('/bar')
        def bar(bar):
            return unicode(bar)

        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/1', url_defaults={'bar': 23})
        app.register_blueprint(bp, url_prefix='/2', url_defaults={'bar': 19})

        c = app.test_client()
        self.assertEqual(c.get('/1/foo').data, u'23/42')
        self.assertEqual(c.get('/2/foo').data, u'19/42')
        self.assertEqual(c.get('/1/bar').data, u'23')
        self.assertEqual(c.get('/2/bar').data, u'19')

    def test_blueprint_url_processors(self):
        bp = flask.Blueprint('frontend', __name__, url_prefix='/<lang_code>')

        @bp.url_defaults
        def add_language_code(endpoint, values):
            values.setdefault('lang_code', flask.g.lang_code)

        @bp.url_value_preprocessor
        def pull_lang_code(endpoint, values):
            flask.g.lang_code = values.pop('lang_code')

        @bp.route('/')
        def index():
            return flask.url_for('.about')

        @bp.route('/about')
        def about():
            return flask.url_for('.index')

        app = flask.Flask(__name__)
        app.register_blueprint(bp)

        c = app.test_client()

        self.assertEqual(c.get('/de/').data, '/de/about')
        self.assertEqual(c.get('/de/about').data, '/de/')

    def test_templates_and_static(self):
        from blueprintapp import app
        c = app.test_client()

        rv = c.get('/')
        assert rv.data == 'Hello from the Frontend'
        rv = c.get('/admin/')
        assert rv.data == 'Hello from the Admin'
        rv = c.get('/admin/index2')
        assert rv.data == 'Hello from the Admin'
        rv = c.get('/admin/static/test.txt')
        assert rv.data.strip() == 'Admin File'
        rv = c.get('/admin/static/css/test.css')
        assert rv.data.strip() == '/* nested file */'

        with app.test_request_context():
            assert flask.url_for('admin.static', filename='test.txt') \
                == '/admin/static/test.txt'

        with app.test_request_context():
            try:
                flask.render_template('missing.html')
            except TemplateNotFound, e:
                assert e.name == 'missing.html'
            else:
                assert 0, 'expected exception'

        with flask.Flask(__name__).test_request_context():
            assert flask.render_template('nested/nested.txt') == 'I\'m nested'

    def test_templates_list(self):
        from blueprintapp import app
        templates = sorted(app.jinja_env.list_templates())
        self.assertEqual(templates, ['admin/index.html',
                                     'frontend/index.html'])

    def test_dotted_names(self):
        frontend = flask.Blueprint('myapp.frontend', __name__)
        backend = flask.Blueprint('myapp.backend', __name__)

        @frontend.route('/fe')
        def frontend_index():
            return flask.url_for('myapp.backend.backend_index')

        @frontend.route('/fe2')
        def frontend_page2():
            return flask.url_for('.frontend_index')

        @backend.route('/be')
        def backend_index():
            return flask.url_for('myapp.frontend.frontend_index')

        app = flask.Flask(__name__)
        app.register_blueprint(frontend)
        app.register_blueprint(backend)

        c = app.test_client()
        self.assertEqual(c.get('/fe').data.strip(), '/be')
        self.assertEqual(c.get('/fe2').data.strip(), '/fe')
        self.assertEqual(c.get('/be').data.strip(), '/fe')

    def test_empty_url_defaults(self):
        bp = flask.Blueprint('bp', __name__)

        @bp.route('/', defaults={'page': 1})
        @bp.route('/page/<int:page>')
        def something(page):
            return str(page)

        app = flask.Flask(__name__)
        app.register_blueprint(bp)

        c = app.test_client()
        self.assertEqual(c.get('/').data, '1')
        self.assertEqual(c.get('/page/2').data, '2')


class SendfileTestCase(unittest.TestCase):

    def test_send_file_regular(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            assert rv.direct_passthrough
            assert rv.mimetype == 'text/html'
            with app.open_resource('static/index.html') as f:
                assert rv.data == f.read()

    def test_send_file_xsendfile(self):
        app = flask.Flask(__name__)
        app.use_x_sendfile = True
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            assert rv.direct_passthrough
            assert 'x-sendfile' in rv.headers
            assert rv.headers['x-sendfile'] == \
                os.path.join(app.root_path, 'static/index.html')
            assert rv.mimetype == 'text/html'

    def test_send_file_object(self):
        app = flask.Flask(__name__)
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f)
                with app.open_resource('static/index.html') as f:
                    assert rv.data == f.read()
                assert rv.mimetype == 'text/html'
            # mimetypes + etag
            assert len(captured) == 2

        app.use_x_sendfile = True
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f)
                assert rv.mimetype == 'text/html'
                assert 'x-sendfile' in rv.headers
                assert rv.headers['x-sendfile'] == \
                    os.path.join(app.root_path, 'static/index.html')
            # mimetypes + etag
            assert len(captured) == 2

        app.use_x_sendfile = False
        with app.test_request_context():
            with catch_warnings() as captured:
                f = StringIO('Test')
                rv = flask.send_file(f)
                assert rv.data == 'Test'
                assert rv.mimetype == 'application/octet-stream'
            # etags
            assert len(captured) == 1
            with catch_warnings() as captured:
                f = StringIO('Test')
                rv = flask.send_file(f, mimetype='text/plain')
                assert rv.data == 'Test'
                assert rv.mimetype == 'text/plain'
            # etags
            assert len(captured) == 1

        app.use_x_sendfile = True
        with catch_warnings() as captured:
            with app.test_request_context():
                f = StringIO('Test')
                rv = flask.send_file(f)
                assert 'x-sendfile' not in rv.headers
            # etags
            assert len(captured) == 1

    def test_attachment(self):
        app = flask.Flask(__name__)
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f, as_attachment=True)
                value, options = parse_options_header(rv.headers['Content-Disposition'])
                assert value == 'attachment'
            # mimetypes + etag
            assert len(captured) == 2

        with app.test_request_context():
            assert options['filename'] == 'index.html'
            rv = flask.send_file('static/index.html', as_attachment=True)
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            assert value == 'attachment'
            assert options['filename'] == 'index.html'

        with app.test_request_context():
            rv = flask.send_file(StringIO('Test'), as_attachment=True,
                                 attachment_filename='index.txt',
                                 add_etags=False)
            assert rv.mimetype == 'text/plain'
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            assert value == 'attachment'
            assert options['filename'] == 'index.txt'


class LoggingTestCase(unittest.TestCase):

    def test_logger_cache(self):
        app = flask.Flask(__name__)
        logger1 = app.logger
        assert app.logger is logger1
        assert logger1.name == __name__
        app.logger_name = __name__ + '/test_logger_cache'
        assert app.logger is not logger1

    def test_debug_log(self):
        app = flask.Flask(__name__)
        app.debug = True

        @app.route('/')
        def index():
            app.logger.warning('the standard library is dead')
            app.logger.debug('this is a debug statement')
            return ''

        @app.route('/exc')
        def exc():
            1/0
        c = app.test_client()

        with catch_stderr() as err:
            c.get('/')
            out = err.getvalue()
            assert 'WARNING in flask_tests [' in out
            assert 'flask_tests.py' in out
            assert 'the standard library is dead' in out
            assert 'this is a debug statement' in out

        with catch_stderr() as err:
            try:
                c.get('/exc')
            except ZeroDivisionError:
                pass
            else:
                assert False, 'debug log ate the exception'

    def test_exception_logging(self):
        out = StringIO()
        app = flask.Flask(__name__)
        app.logger_name = 'flask_tests/test_exception_logging'
        app.logger.addHandler(StreamHandler(out))

        @app.route('/')
        def index():
            1/0

        rv = app.test_client().get('/')
        assert rv.status_code == 500
        assert 'Internal Server Error' in rv.data

        err = out.getvalue()
        assert 'Exception on / [GET]' in err
        assert 'Traceback (most recent call last):' in err
        assert '1/0' in err
        assert 'ZeroDivisionError:' in err

    def test_processor_exceptions(self):
        app = flask.Flask(__name__)
        @app.before_request
        def before_request():
            if trigger == 'before':
                1/0
        @app.after_request
        def after_request(response):
            if trigger == 'after':
                1/0
            return response
        @app.route('/')
        def index():
            return 'Foo'
        @app.errorhandler(500)
        def internal_server_error(e):
            return 'Hello Server Error', 500
        for trigger in 'before', 'after':
            rv = app.test_client().get('/')
            assert rv.status_code == 500
            assert rv.data == 'Hello Server Error'


class ConfigTestCase(unittest.TestCase):

    def common_object_test(self, app):
        assert app.secret_key == 'devkey'
        assert app.config['TEST_KEY'] == 'foo'
        assert 'ConfigTestCase' not in app.config

    def test_config_from_file(self):
        app = flask.Flask(__name__)
        app.config.from_pyfile('flask_tests.py')
        self.common_object_test(app)

    def test_config_from_object(self):
        app = flask.Flask(__name__)
        app.config.from_object(__name__)
        self.common_object_test(app)

    def test_config_from_class(self):
        class Base(object):
            TEST_KEY = 'foo'
        class Test(Base):
            SECRET_KEY = 'devkey'
        app = flask.Flask(__name__)
        app.config.from_object(Test)
        self.common_object_test(app)

    def test_config_from_envvar(self):
        import os
        env = os.environ
        try:
            os.environ = {}
            app = flask.Flask(__name__)
            try:
                app.config.from_envvar('FOO_SETTINGS')
            except RuntimeError, e:
                assert "'FOO_SETTINGS' is not set" in str(e)
            else:
                assert 0, 'expected exception'
            assert not app.config.from_envvar('FOO_SETTINGS', silent=True)

            os.environ = {'FOO_SETTINGS': 'flask_tests.py'}
            assert app.config.from_envvar('FOO_SETTINGS')
            self.common_object_test(app)
        finally:
            os.environ = env

    def test_config_missing(self):
        app = flask.Flask(__name__)
        try:
            app.config.from_pyfile('missing.cfg')
        except IOError, e:
            msg = str(e)
            assert msg.startswith('[Errno 2] Unable to load configuration '
                                  'file (No such file or directory):')
            assert msg.endswith("missing.cfg'")
        else:
            assert 0, 'expected config'
        assert not app.config.from_pyfile('missing.cfg', silent=True)


class SubdomainTestCase(unittest.TestCase):

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
        assert rv.data == 'normal index'

        rv = c.get('/', 'http://test.localhost/')
        assert rv.data == 'test index'

    @emits_module_deprecation_warning
    def test_module_static_path_subdomain(self):
        app = flask.Flask(__name__)
        app.config['SERVER_NAME'] = 'example.com'
        from subdomaintestmodule import mod
        app.register_module(mod)
        c = app.test_client()
        rv = c.get('/static/hello.txt', 'http://foo.example.com/')
        assert rv.data.strip() == 'Hello Subdomain'

    def test_subdomain_matching(self):
        app = flask.Flask(__name__)
        app.config['SERVER_NAME'] = 'localhost'
        @app.route('/', subdomain='<user>')
        def index(user):
            return 'index for %s' % user

        c = app.test_client()
        rv = c.get('/', 'http://mitsuhiko.localhost/')
        assert rv.data == 'index for mitsuhiko'

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
        assert rv.data == 'Test'
        rv = c.get('/outside', 'http://xtesting.localhost/')
        assert rv.data == 'Outside'


class TestSignals(unittest.TestCase):

    def test_template_rendered(self):
        app = flask.Flask(__name__)

        @app.route('/')
        def index():
            return flask.render_template('simple_template.html', whiskey=42)

        recorded = []
        def record(sender, template, context):
            recorded.append((template, context))

        flask.template_rendered.connect(record, app)
        try:
            app.test_client().get('/')
            assert len(recorded) == 1
            template, context = recorded[0]
            assert template.name == 'simple_template.html'
            assert context['whiskey'] == 42
        finally:
            flask.template_rendered.disconnect(record, app)

    def test_request_signals(self):
        app = flask.Flask(__name__)
        calls = []

        def before_request_signal(sender):
            calls.append('before-signal')

        def after_request_signal(sender, response):
            assert response.data == 'stuff'
            calls.append('after-signal')

        @app.before_request
        def before_request_handler():
            calls.append('before-handler')

        @app.after_request
        def after_request_handler(response):
            calls.append('after-handler')
            response.data = 'stuff'
            return response

        @app.route('/')
        def index():
            calls.append('handler')
            return 'ignored anyway'

        flask.request_started.connect(before_request_signal, app)
        flask.request_finished.connect(after_request_signal, app)

        try:
            rv = app.test_client().get('/')
            assert rv.data == 'stuff'

            assert calls == ['before-signal', 'before-handler',
                             'handler', 'after-handler',
                             'after-signal']
        finally:
            flask.request_started.disconnect(before_request_signal, app)
            flask.request_finished.disconnect(after_request_signal, app)

    def test_request_exception_signal(self):
        app = flask.Flask(__name__)
        recorded = []

        @app.route('/')
        def index():
            1/0

        def record(sender, exception):
            recorded.append(exception)

        flask.got_request_exception.connect(record, app)
        try:
            assert app.test_client().get('/').status_code == 500
            assert len(recorded) == 1
            assert isinstance(recorded[0], ZeroDivisionError)
        finally:
            flask.got_request_exception.disconnect(record, app)


class ViewTestCase(unittest.TestCase):

    def common_test(self, app):
        c = app.test_client()

        self.assertEqual(c.get('/').data, 'GET')
        self.assertEqual(c.post('/').data, 'POST')
        self.assertEqual(c.put('/').status_code, 405)
        meths = parse_set_header(c.open('/', method='OPTIONS').headers['Allow'])
        self.assertEqual(sorted(meths), ['GET', 'HEAD', 'OPTIONS', 'POST'])

    def test_basic_view(self):
        app = flask.Flask(__name__)

        class Index(flask.views.View):
            methods = ['GET', 'POST']
            def dispatch_request(self):
                return flask.request.method

        app.add_url_rule('/', view_func=Index.as_view('index'))
        self.common_test(app)

    def test_method_based_view(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                return 'GET'
            def post(self):
                return 'POST'

        app.add_url_rule('/', view_func=Index.as_view('index'))

        self.common_test(app)

    def test_view_patching(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                1/0
            def post(self):
                1/0

        class Other(Index):
            def get(self):
                return 'GET'
            def post(self):
                return 'POST'

        view = Index.as_view('index')
        view.view_class = Other
        app.add_url_rule('/', view_func=view)
        self.common_test(app)

    def test_view_inheritance(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                return 'GET'
            def post(self):
                return 'POST'

        class BetterIndex(Index):
            def delete(self):
                return 'DELETE'

        app.add_url_rule('/', view_func=BetterIndex.as_view('index'))
        c = app.test_client()

        meths = parse_set_header(c.open('/', method='OPTIONS').headers['Allow'])
        self.assertEqual(sorted(meths), ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST'])


class DeprecationsTestCase(unittest.TestCase):

    def test_init_jinja_globals(self):
        class MyFlask(flask.Flask):
            def init_jinja_globals(self):
                self.jinja_env.globals['foo'] = '42'

        with catch_warnings() as log:
            app = MyFlask(__name__)
            @app.route('/')
            def foo():
                return app.jinja_env.globals['foo']

            c = app.test_client()
            assert c.get('/').data == '42'
            assert len(log) == 1
            assert 'init_jinja_globals' in str(log[0]['message'])


def suite():
    from minitwit_tests import MiniTwitTestCase
    from flaskr_tests import FlaskrTestCase
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContextTestCase))
    suite.addTest(unittest.makeSuite(BasicFunctionalityTestCase))
    suite.addTest(unittest.makeSuite(TemplatingTestCase))
    suite.addTest(unittest.makeSuite(ModuleTestCase))
    suite.addTest(unittest.makeSuite(BlueprintTestCase))
    suite.addTest(unittest.makeSuite(SendfileTestCase))
    suite.addTest(unittest.makeSuite(LoggingTestCase))
    suite.addTest(unittest.makeSuite(ConfigTestCase))
    suite.addTest(unittest.makeSuite(SubdomainTestCase))
    suite.addTest(unittest.makeSuite(ViewTestCase))
    suite.addTest(unittest.makeSuite(DeprecationsTestCase))
    suite.addTest(unittest.makeSuite(InstanceTestCase))
    if flask.json_available:
        suite.addTest(unittest.makeSuite(JSONTestCase))
    if flask.signals_available:
        suite.addTest(unittest.makeSuite(TestSignals))
    suite.addTest(unittest.makeSuite(MiniTwitTestCase))
    suite.addTest(unittest.makeSuite(FlaskrTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
