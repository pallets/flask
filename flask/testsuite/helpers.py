# -*- coding: utf-8 -*-
"""
    flask.testsuite.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Various helpers.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import os
import flask
import unittest
from logging import StreamHandler
from StringIO import StringIO
from flask.testsuite import FlaskTestCase, catch_warnings, catch_stderr
from werkzeug.http import parse_cache_control_header, parse_options_header


def has_encoding(name):
    try:
        import codecs
        codecs.lookup(name)
        return True
    except LookupError:
        return False


class JSONTestCase(FlaskTestCase):

    def test_json_bad_requests(self):
        app = flask.Flask(__name__)
        @app.route('/json', methods=['POST'])
        def return_json():
            return unicode(flask.request.json)
        c = app.test_client()
        rv = c.post('/json', data='malformed', content_type='application/json')
        self.assert_equal(rv.status_code, 400)

    def test_json_bad_requests_content_type(self):
        app = flask.Flask(__name__)
        @app.route('/json', methods=['POST'])
        def return_json():
            return unicode(flask.request.json)
        c = app.test_client()
        rv = c.post('/json', data='malformed', content_type='application/json')
        self.assert_equal(rv.status_code, 400)
        self.assert_equal(rv.mimetype, 'application/json')
        self.assert_('description' in flask.json.loads(rv.data))
        self.assert_('<p>' not in flask.json.loads(rv.data)['description'])

    def test_json_body_encoding(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            return flask.request.json

        c = app.test_client()
        resp = c.get('/', data=u'"Hällo Wörld"'.encode('iso-8859-15'),
                     content_type='application/json; charset=iso-8859-15')
        self.assert_equal(resp.data, u'Hällo Wörld'.encode('utf-8'))

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
            self.assert_equal(rv.mimetype, 'application/json')
            self.assert_equal(flask.json.loads(rv.data), d)

    def test_json_attr(self):
        app = flask.Flask(__name__)
        @app.route('/add', methods=['POST'])
        def add():
            return unicode(flask.request.json['a'] + flask.request.json['b'])
        c = app.test_client()
        rv = c.post('/add', data=flask.json.dumps({'a': 1, 'b': 2}),
                            content_type='application/json')
        self.assert_equal(rv.data, '3')

    def test_template_escaping(self):
        app = flask.Flask(__name__)
        render = flask.render_template_string
        with app.test_request_context():
            rv = render('{{ "</script>"|tojson|safe }}')
            self.assert_equal(rv, '"<\\/script>"')
            rv = render('{{ "<\0/script>"|tojson|safe }}')
            self.assert_equal(rv, '"<\\u0000\\/script>"')

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
        self.assert_equal(rv.status_code, 200)
        self.assert_equal(rv.data, u'정상처리'.encode('utf-8'))

    if not has_encoding('euc-kr'):
        test_modified_url_encoding = None


class SendfileTestCase(FlaskTestCase):

    def test_send_file_regular(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            self.assert_(rv.direct_passthrough)
            self.assert_equal(rv.mimetype, 'text/html')
            with app.open_resource('static/index.html') as f:
                self.assert_equal(rv.data, f.read())

    def test_send_file_xsendfile(self):
        app = flask.Flask(__name__)
        app.use_x_sendfile = True
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            self.assert_(rv.direct_passthrough)
            self.assert_('x-sendfile' in rv.headers)
            self.assert_equal(rv.headers['x-sendfile'],
                os.path.join(app.root_path, 'static/index.html'))
            self.assert_equal(rv.mimetype, 'text/html')

    def test_send_file_object(self):
        app = flask.Flask(__name__)
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f)
                with app.open_resource('static/index.html') as f:
                    self.assert_equal(rv.data, f.read())
                self.assert_equal(rv.mimetype, 'text/html')
            # mimetypes + etag
            self.assert_equal(len(captured), 2)

        app.use_x_sendfile = True
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f)
                self.assert_equal(rv.mimetype, 'text/html')
                self.assert_('x-sendfile' in rv.headers)
                self.assert_equal(rv.headers['x-sendfile'],
                    os.path.join(app.root_path, 'static/index.html'))
            # mimetypes + etag
            self.assert_equal(len(captured), 2)

        app.use_x_sendfile = False
        with app.test_request_context():
            with catch_warnings() as captured:
                f = StringIO('Test')
                rv = flask.send_file(f)
                self.assert_equal(rv.data, 'Test')
                self.assert_equal(rv.mimetype, 'application/octet-stream')
            # etags
            self.assert_equal(len(captured), 1)
            with catch_warnings() as captured:
                f = StringIO('Test')
                rv = flask.send_file(f, mimetype='text/plain')
                self.assert_equal(rv.data, 'Test')
                self.assert_equal(rv.mimetype, 'text/plain')
            # etags
            self.assert_equal(len(captured), 1)

        app.use_x_sendfile = True
        with catch_warnings() as captured:
            with app.test_request_context():
                f = StringIO('Test')
                rv = flask.send_file(f)
                self.assert_('x-sendfile' not in rv.headers)
            # etags
            self.assert_equal(len(captured), 1)

    def test_attachment(self):
        app = flask.Flask(__name__)
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f, as_attachment=True)
                value, options = parse_options_header(rv.headers['Content-Disposition'])
                self.assert_equal(value, 'attachment')
            # mimetypes + etag
            self.assert_equal(len(captured), 2)

        with app.test_request_context():
            self.assert_equal(options['filename'], 'index.html')
            rv = flask.send_file('static/index.html', as_attachment=True)
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            self.assert_equal(value, 'attachment')
            self.assert_equal(options['filename'], 'index.html')

        with app.test_request_context():
            rv = flask.send_file(StringIO('Test'), as_attachment=True,
                                 attachment_filename='index.txt',
                                 add_etags=False)
            self.assert_equal(rv.mimetype, 'text/plain')
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            self.assert_equal(value, 'attachment')
            self.assert_equal(options['filename'], 'index.txt')

    def test_static_file(self):
        app = flask.Flask(__name__)
        # default cache timeout is 12 hours
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 12 * 60 * 60)
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 12 * 60 * 60)
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 3600)
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 3600)
        class StaticFileApp(flask.Flask):
            def get_send_file_max_age(self, filename):
                return 10
        app = StaticFileApp(__name__)
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 10)
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 10)


class LoggingTestCase(FlaskTestCase):

    def test_logger_cache(self):
        app = flask.Flask(__name__)
        logger1 = app.logger
        self.assert_(app.logger is logger1)
        self.assert_equal(logger1.name, __name__)
        app.logger_name = __name__ + '/test_logger_cache'
        self.assert_(app.logger is not logger1)

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

        with app.test_client() as c:
            with catch_stderr() as err:
                c.get('/')
                out = err.getvalue()
                self.assert_('WARNING in helpers [' in out)
                self.assert_(os.path.basename(__file__.rsplit('.', 1)[0] + '.py') in out)
                self.assert_('the standard library is dead' in out)
                self.assert_('this is a debug statement' in out)

            with catch_stderr() as err:
                try:
                    c.get('/exc')
                except ZeroDivisionError:
                    pass
                else:
                    self.assert_(False, 'debug log ate the exception')

    def test_debug_log_override(self):
        app = flask.Flask(__name__)
        app.debug = True
        app.logger_name = 'flask_tests/test_debug_log_override'
        app.logger.level = 10
        self.assert_equal(app.logger.level, 10)

    def test_exception_logging(self):
        out = StringIO()
        app = flask.Flask(__name__)
        app.logger_name = 'flask_tests/test_exception_logging'
        app.logger.addHandler(StreamHandler(out))

        @app.route('/')
        def index():
            1/0

        rv = app.test_client().get('/')
        self.assert_equal(rv.status_code, 500)
        self.assert_('Internal Server Error' in rv.data)

        err = out.getvalue()
        self.assert_('Exception on / [GET]' in err)
        self.assert_('Traceback (most recent call last):' in err)
        self.assert_('1/0' in err)
        self.assert_('ZeroDivisionError:' in err)

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
            self.assert_equal(rv.status_code, 500)
            self.assert_equal(rv.data, 'Hello Server Error')

    def test_url_for_with_anchor(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            self.assert_equal(flask.url_for('index', _anchor='x y'),
                              '/#x%20y')

    def test_url_with_method(self):
        from flask.views import MethodView
        app = flask.Flask(__name__)
        class MyView(MethodView):
            def get(self, id=None):
                if id is None:
                    return 'List'
                return 'Get %d' % id
            def post(self):
                return 'Create'
        myview = MyView.as_view('myview')
        app.add_url_rule('/myview/', methods=['GET'],
                         view_func=myview)
        app.add_url_rule('/myview/<int:id>', methods=['GET'],
                         view_func=myview)
        app.add_url_rule('/myview/create', methods=['POST'],
                         view_func=myview)

        with app.test_request_context():
            self.assert_equal(flask.url_for('myview', _method='GET'),
                              '/myview/')
            self.assert_equal(flask.url_for('myview', id=42, _method='GET'),
                              '/myview/42')
            self.assert_equal(flask.url_for('myview', _method='POST'),
                              '/myview/create')


class NoImportsTestCase(FlaskTestCase):
    """Test Flasks are created without import.

    Avoiding ``__import__`` helps create Flask instances where there are errors
    at import time.  Those runtime errors will be apparent to the user soon
    enough, but tools which build Flask instances meta-programmatically benefit
    from a Flask which does not ``__import__``.  Instead of importing to
    retrieve file paths or metadata on a module or package, use the pkgutil and
    imp modules in the Python standard library.
    """

    def test_name_with_import_error(self):
        try:
            flask.Flask('importerror')
        except NotImplementedError:
            self.fail('Flask(import_name) is importing import_name.')


class StreamingTestCase(FlaskTestCase):

    def test_streaming_with_context(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            def generate():
                yield 'Hello '
                yield flask.request.args['name']
                yield '!'
            return flask.Response(flask.stream_with_context(generate()))
        c = app.test_client()
        rv = c.get('/?name=World')
        self.assertEqual(rv.data, 'Hello World!')

    def test_streaming_with_context_as_decorator(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            @flask.stream_with_context
            def generate():
                yield 'Hello '
                yield flask.request.args['name']
                yield '!'
            return flask.Response(generate())
        c = app.test_client()
        rv = c.get('/?name=World')
        self.assertEqual(rv.data, 'Hello World!')

    def test_streaming_with_context_and_custom_close(self):
        app = flask.Flask(__name__)
        app.testing = True
        called = []
        class Wrapper(object):
            def __init__(self, gen):
                self._gen = gen
            def __iter__(self):
                return self
            def close(self):
                called.append(42)
            def next(self):
                return self._gen.next()
        @app.route('/')
        def index():
            def generate():
                yield 'Hello '
                yield flask.request.args['name']
                yield '!'
            return flask.Response(flask.stream_with_context(
                Wrapper(generate())))
        c = app.test_client()
        rv = c.get('/?name=World')
        self.assertEqual(rv.data, 'Hello World!')
        self.assertEqual(called, [42])


def suite():
    suite = unittest.TestSuite()
    if flask.json_available:
        suite.addTest(unittest.makeSuite(JSONTestCase))
    suite.addTest(unittest.makeSuite(SendfileTestCase))
    suite.addTest(unittest.makeSuite(LoggingTestCase))
    suite.addTest(unittest.makeSuite(NoImportsTestCase))
    suite.addTest(unittest.makeSuite(StreamingTestCase))
    return suite
