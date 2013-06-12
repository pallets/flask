# -*- coding: utf-8 -*-
"""
    flask.testsuite.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Various helpers.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import flask
import unittest
from logging import StreamHandler
from flask.testsuite import FlaskTestCase, catch_warnings, catch_stderr
from werkzeug.http import parse_cache_control_header, parse_options_header
from flask._compat import StringIO, text_type


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
            return flask.jsonify(foo=text_type(flask.request.get_json()))
        c = app.test_client()
        rv = c.post('/json', data='malformed', content_type='application/json')
        self.assert_equal(rv.status_code, 400)

    def test_json_body_encoding(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            return flask.request.get_json()

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

    def test_json_as_unicode(self):
        app = flask.Flask(__name__)

        app.config['JSON_AS_ASCII'] = True
        with app.app_context():
            rv = flask.json.dumps(u'\N{SNOWMAN}')
            self.assert_equal(rv, '"\\u2603"')

        app.config['JSON_AS_ASCII'] = False
        with app.app_context():
            rv = flask.json.dumps(u'\N{SNOWMAN}')
            self.assert_equal(rv, u'"\u2603"')

    def test_json_attr(self):
        app = flask.Flask(__name__)
        @app.route('/add', methods=['POST'])
        def add():
            json = flask.request.get_json()
            return text_type(json['a'] + json['b'])
        c = app.test_client()
        rv = c.post('/add', data=flask.json.dumps({'a': 1, 'b': 2}),
                            content_type='application/json')
        self.assert_equal(rv.data, b'3')

    def test_template_escaping(self):
        app = flask.Flask(__name__)
        render = flask.render_template_string
        with app.test_request_context():
            rv = flask.json.htmlsafe_dumps('</script>')
            self.assert_equal(rv, u'"\\u003c/script\\u003e"')
            self.assert_equal(type(rv), text_type)
            rv = render('{{ "</script>"|tojson }}')
            self.assert_equal(rv, '"\\u003c/script\\u003e"')
            rv = render('{{ "<\0/script>"|tojson }}')
            self.assert_equal(rv, '"\\u003c\\u0000/script\\u003e"')
            rv = render('{{ "<!--<script>"|tojson }}')
            self.assert_equal(rv, '"\\u003c!--\\u003cscript\\u003e"')
            rv = render('{{ "&"|tojson }}')
            self.assert_equal(rv, '"\\u0026"')

    def test_json_customization(self):
        class X(object):
            def __init__(self, val):
                self.val = val
        class MyEncoder(flask.json.JSONEncoder):
            def default(self, o):
                if isinstance(o, X):
                    return '<%d>' % o.val
                return flask.json.JSONEncoder.default(self, o)
        class MyDecoder(flask.json.JSONDecoder):
            def __init__(self, *args, **kwargs):
                kwargs.setdefault('object_hook', self.object_hook)
                flask.json.JSONDecoder.__init__(self, *args, **kwargs)
            def object_hook(self, obj):
                if len(obj) == 1 and '_foo' in obj:
                    return X(obj['_foo'])
                return obj
        app = flask.Flask(__name__)
        app.testing = True
        app.json_encoder = MyEncoder
        app.json_decoder = MyDecoder
        @app.route('/', methods=['POST'])
        def index():
            return flask.json.dumps(flask.request.get_json()['x'])
        c = app.test_client()
        rv = c.post('/', data=flask.json.dumps({
            'x': {'_foo': 42}
        }), content_type='application/json')
        self.assertEqual(rv.data, b'"<42>"')

    def test_modified_url_encoding(self):
        class ModifiedRequest(flask.Request):
            url_charset = 'euc-kr'
        app = flask.Flask(__name__)
        app.testing = True
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

    def test_json_key_sorting(self):
        app = flask.Flask(__name__)
        app.testing = True
        self.assert_equal(app.config['JSON_SORT_KEYS'], True)
        d = dict.fromkeys(range(20), 'foo')

        @app.route('/')
        def index():
            return flask.jsonify(values=d)

        c = app.test_client()
        rv = c.get('/')
        lines = [x.strip() for x in rv.data.strip().decode('utf-8').splitlines()]
        self.assert_equal(lines, [
            '{',
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
            '}',
            '}'
        ])


class SendfileTestCase(FlaskTestCase):

    def test_send_file_regular(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            self.assert_true(rv.direct_passthrough)
            self.assert_equal(rv.mimetype, 'text/html')
            with app.open_resource('static/index.html') as f:
                rv.direct_passthrough = False
                self.assert_equal(rv.data, f.read())
            rv.close()

    def test_send_file_xsendfile(self):
        app = flask.Flask(__name__)
        app.use_x_sendfile = True
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            self.assert_true(rv.direct_passthrough)
            self.assert_in('x-sendfile', rv.headers)
            self.assert_equal(rv.headers['x-sendfile'],
                os.path.join(app.root_path, 'static/index.html'))
            self.assert_equal(rv.mimetype, 'text/html')
            rv.close()

    def test_send_file_object(self):
        app = flask.Flask(__name__)
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f)
                rv.direct_passthrough = False
                with app.open_resource('static/index.html') as f:
                    self.assert_equal(rv.data, f.read())
                self.assert_equal(rv.mimetype, 'text/html')
                rv.close()
            # mimetypes + etag
            self.assert_equal(len(captured), 2)

        app.use_x_sendfile = True
        with catch_warnings() as captured:
            with app.test_request_context():
                f = open(os.path.join(app.root_path, 'static/index.html'))
                rv = flask.send_file(f)
                self.assert_equal(rv.mimetype, 'text/html')
                self.assert_in('x-sendfile', rv.headers)
                self.assert_equal(rv.headers['x-sendfile'],
                    os.path.join(app.root_path, 'static/index.html'))
                rv.close()
            # mimetypes + etag
            self.assert_equal(len(captured), 2)

        app.use_x_sendfile = False
        with app.test_request_context():
            with catch_warnings() as captured:
                f = StringIO('Test')
                rv = flask.send_file(f)
                rv.direct_passthrough = False
                self.assert_equal(rv.data, b'Test')
                self.assert_equal(rv.mimetype, 'application/octet-stream')
                rv.close()
            # etags
            self.assert_equal(len(captured), 1)
            with catch_warnings() as captured:
                f = StringIO('Test')
                rv = flask.send_file(f, mimetype='text/plain')
                rv.direct_passthrough = False
                self.assert_equal(rv.data, b'Test')
                self.assert_equal(rv.mimetype, 'text/plain')
                rv.close()
            # etags
            self.assert_equal(len(captured), 1)

        app.use_x_sendfile = True
        with catch_warnings() as captured:
            with app.test_request_context():
                f = StringIO('Test')
                rv = flask.send_file(f)
                self.assert_not_in('x-sendfile', rv.headers)
                rv.close()
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
                rv.close()
            # mimetypes + etag
            self.assert_equal(len(captured), 2)

        with app.test_request_context():
            self.assert_equal(options['filename'], 'index.html')
            rv = flask.send_file('static/index.html', as_attachment=True)
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            self.assert_equal(value, 'attachment')
            self.assert_equal(options['filename'], 'index.html')
            rv.close()

        with app.test_request_context():
            rv = flask.send_file(StringIO('Test'), as_attachment=True,
                                 attachment_filename='index.txt',
                                 add_etags=False)
            self.assert_equal(rv.mimetype, 'text/plain')
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            self.assert_equal(value, 'attachment')
            self.assert_equal(options['filename'], 'index.txt')
            rv.close()

    def test_static_file(self):
        app = flask.Flask(__name__)
        # default cache timeout is 12 hours
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 12 * 60 * 60)
            rv.close()
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 12 * 60 * 60)
            rv.close()
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 3600)
            rv.close()
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 3600)
            rv.close()
        class StaticFileApp(flask.Flask):
            def get_send_file_max_age(self, filename):
                return 10
        app = StaticFileApp(__name__)
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 10)
            rv.close()
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, 10)
            rv.close()


class LoggingTestCase(FlaskTestCase):

    def test_logger_cache(self):
        app = flask.Flask(__name__)
        logger1 = app.logger
        self.assert_true(app.logger is logger1)
        self.assert_equal(logger1.name, __name__)
        app.logger_name = __name__ + '/test_logger_cache'
        self.assert_true(app.logger is not logger1)

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
            1 // 0

        with app.test_client() as c:
            with catch_stderr() as err:
                c.get('/')
                out = err.getvalue()
                self.assert_in('WARNING in helpers [', out)
                self.assert_in(os.path.basename(__file__.rsplit('.', 1)[0] + '.py'), out)
                self.assert_in('the standard library is dead', out)
                self.assert_in('this is a debug statement', out)

            with catch_stderr() as err:
                try:
                    c.get('/exc')
                except ZeroDivisionError:
                    pass
                else:
                    self.assert_true(False, 'debug log ate the exception')

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
            1 // 0

        rv = app.test_client().get('/')
        self.assert_equal(rv.status_code, 500)
        self.assert_in(b'Internal Server Error', rv.data)

        err = out.getvalue()
        self.assert_in('Exception on / [GET]', err)
        self.assert_in('Traceback (most recent call last):', err)
        self.assert_in('1 // 0', err)
        self.assert_in('ZeroDivisionError:', err)

    def test_processor_exceptions(self):
        app = flask.Flask(__name__)
        @app.before_request
        def before_request():
            if trigger == 'before':
                1 // 0
        @app.after_request
        def after_request(response):
            if trigger == 'after':
                1 // 0
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
            self.assert_equal(rv.data, b'Hello Server Error')

    def test_url_for_with_anchor(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            self.assert_equal(flask.url_for('index', _anchor='x y'),
                              '/#x%20y')

    def test_url_for_with_scheme(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            self.assert_equal(flask.url_for('index',
                                            _external=True,
                                            _scheme='https'),
                              'https://localhost/')

    def test_url_for_with_scheme_not_external(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            self.assert_raises(ValueError,
                               flask.url_for,
                               'index',
                               _scheme='https')

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
        self.assertEqual(rv.data, b'Hello World!')

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
        self.assertEqual(rv.data, b'Hello World!')

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
            def __next__(self):
                return next(self._gen)
            next = __next__
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
        self.assertEqual(rv.data, b'Hello World!')
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
