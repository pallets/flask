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
from StringIO import StringIO
from flask.testsuite import FlaskTestCase, catch_warnings, catch_stderr
from werkzeug.http import parse_options_header


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


class SendfileTestCase(FlaskTestCase):

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


class LoggingTestCase(FlaskTestCase):

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

        with app.test_client() as c:
            with catch_stderr() as err:
                c.get('/')
                out = err.getvalue()
                assert 'WARNING in helpers [' in out
                assert os.path.basename(__file__.rsplit('.')[0] + '.py') in out
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


def suite():
    suite = unittest.TestSuite()
    if flask.json_available:
        suite.addTest(unittest.makeSuite(JSONTestCase))
    suite.addTest(unittest.makeSuite(SendfileTestCase))
    suite.addTest(unittest.makeSuite(LoggingTestCase))
    return suite
