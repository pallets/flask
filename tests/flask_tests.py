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
import unittest
import tempfile
from contextlib import contextmanager
from datetime import datetime
from werkzeug import parse_date, parse_options_header
from cStringIO import StringIO


example_path = os.path.join(os.path.dirname(__file__), '..', 'examples')
sys.path.append(os.path.join(example_path, 'flaskr'))
sys.path.append(os.path.join(example_path, 'minitwit'))


# config keys used for the ConfigTestCase
TEST_KEY = 'foo'
SECRET_KEY = 'devkey'


@contextmanager
def catch_stderr():
    old_stderr = sys.stderr
    sys.stderr = rv = StringIO()
    try:
        yield rv
    finally:
        sys.stderr = old_stderr


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
        except AttributeError:
            pass
        else:
            assert 0, 'expected runtime error'


class BasicFunctionalityTestCase(unittest.TestCase):

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
        assert sorted(rv.allow) == ['GET', 'HEAD']
        rv = c.head('/')
        assert rv.status_code == 200
        assert not rv.data  # head truncates
        assert c.post('/more').data == 'POST'
        assert c.get('/more').data == 'GET'
        rv = c.delete('/more')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'POST']

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
        assert sorted(rv.allow) == ['GET', 'HEAD']
        rv = c.head('/')
        assert rv.status_code == 200
        assert not rv.data  # head truncates
        assert c.post('/more').data == 'POST'
        assert c.get('/more').data == 'GET'
        rv = c.delete('/more')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'POST']

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
        rv = app.test_client().get('/')
        assert 'set-cookie' in rv.headers
        match = re.search(r'\bexpires=([^;]+)', rv.headers['set-cookie'])
        expires = parse_date(match.group())
        expected = datetime.utcnow() + app.permanent_session_lifetime
        assert expires.year == expected.year
        assert expires.month == expected.month
        assert expires.day == expected.day

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
        assert 'internal server error' in rv.data

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


class JSONTestCase(unittest.TestCase):

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


class ModuleTestCase(unittest.TestCase):

    def test_basic_module(self):
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin', url_prefix='/admin')
        @admin.route('/')
        def index():
            return 'admin index'
        @admin.route('/login')
        def login():
            return 'admin login'
        @admin.route('/logout')
        def logout():
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
        def index():
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
        def index():
            return flask.render_template_string('{{ a }}{{ b }}{{ c }}')
        app.register_module(admin)
        c = app.test_client()
        assert c.get('/').data == '13'
        assert c.get('/admin/').data == '123'

    def test_late_binding(self):
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin')
        @admin.route('/')
        def index():
            return '42'
        app.register_module(admin, url_prefix='/admin')
        assert app.test_client().get('/admin/').data == '42'


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
        with app.test_request_context():
            f = open(os.path.join(app.root_path, 'static/index.html'))
            rv = flask.send_file(f)
            with app.open_resource('static/index.html') as f:
                assert rv.data == f.read()
            assert rv.mimetype == 'text/html'

        app.use_x_sendfile = True
        with app.test_request_context():
            f = open(os.path.join(app.root_path, 'static/index.html'))
            rv = flask.send_file(f)
            assert rv.mimetype == 'text/html'
            assert 'x-sendfile' in rv.headers
            assert rv.headers['x-sendfile'] == \
                os.path.join(app.root_path, 'static/index.html')

        app.use_x_sendfile = False
        with app.test_request_context():
            f = StringIO('Test')
            rv = flask.send_file(f)
            assert rv.data == 'Test'
            assert rv.mimetype == 'application/octet-stream'
            f = StringIO('Test')
            rv = flask.send_file(f, mimetype='text/plain')
            assert rv.data == 'Test'
            assert rv.mimetype == 'text/plain'

        app.use_x_sendfile = True
        with app.test_request_context():
            f = StringIO('Test')
            rv = flask.send_file(f)
            assert 'x-sendfile' not in rv.headers

    def test_attachment(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            f = open(os.path.join(app.root_path, 'static/index.html'))
            rv = flask.send_file(f, as_attachment=True)
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            assert value == 'attachment'

        with app.test_request_context():
            assert options['filename'] == 'index.html'
            rv = flask.send_file('static/index.html', as_attachment=True)
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            assert value == 'attachment'
            assert options['filename'] == 'index.html'

        with app.test_request_context():
            rv = flask.send_file(StringIO('Test'), as_attachment=True,
                                 attachment_filename='index.txt')
            assert rv.mimetype == 'text/plain'
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            assert value == 'attachment'
            assert options['filename'] == 'index.txt'


class LoggingTestCase(unittest.TestCase):

    def test_debug_log(self):
        app = flask.Flask(__name__)
        app.debug = True
        @app.route('/')
        def index():
            app.logger.warning('the standard library is dead')
            return ''

        @app.route('/exc')
        def exc():
            1/0
        c = app.test_client()

        with catch_stderr() as err:
            rv = c.get('/')
            out = err.getvalue()
            assert 'WARNING in flask_tests,' in out
            assert 'flask_tests.py' in out
            assert 'the standard library is dead' in out

        with catch_stderr() as err:
            try:
                c.get('/exc')
            except ZeroDivisionError:
                pass
            else:
                assert False, 'debug log ate the exception'

    def test_exception_logging(self):
        from logging import StreamHandler
        out = StringIO()
        app = flask.Flask(__name__)
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
            not app.config.from_envvar('FOO_SETTINGS', silent=True)

            os.environ = {'FOO_SETTINGS': 'flask_tests.py'}
            assert app.config.from_envvar('FOO_SETTINGS')
            self.common_object_test(app)
        finally:
            os.environ = env


def suite():
    from minitwit_tests import MiniTwitTestCase
    from flaskr_tests import FlaskrTestCase
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ContextTestCase))
    suite.addTest(unittest.makeSuite(BasicFunctionalityTestCase))
    suite.addTest(unittest.makeSuite(TemplatingTestCase))
    suite.addTest(unittest.makeSuite(ModuleTestCase))
    suite.addTest(unittest.makeSuite(SendfileTestCase))
    suite.addTest(unittest.makeSuite(LoggingTestCase))
    suite.addTest(unittest.makeSuite(ConfigTestCase))
    if flask.json_available:
        suite.addTest(unittest.makeSuite(JSONTestCase))
    suite.addTest(unittest.makeSuite(MiniTwitTestCase))
    suite.addTest(unittest.makeSuite(FlaskrTestCase))
    return suite


if __name__ == '__main__':
    unittest.main(defaultTest='suite')
