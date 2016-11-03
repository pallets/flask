# -*- coding: utf-8 -*-
"""
    tests.helpers
    ~~~~~~~~~~~~~~~~~~~~~~~

    Various helpers.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import os
import uuid
import datetime

import flask
from logging import StreamHandler
from werkzeug.datastructures import Range
from werkzeug.exceptions import BadRequest, NotFound
from werkzeug.http import parse_cache_control_header, parse_options_header
from werkzeug.http import http_date
from flask._compat import StringIO, text_type


def has_encoding(name):
    try:
        import codecs
        codecs.lookup(name)
        return True
    except LookupError:
        return False


class TestJSON(object):

    def test_post_empty_json_adds_exception_to_response_content_in_debug(self):
        app = flask.Flask(__name__)
        app.config['DEBUG'] = True
        @app.route('/json', methods=['POST'])
        def post_json():
            flask.request.get_json()
            return None
        c = app.test_client()
        rv = c.post('/json', data=None, content_type='application/json')
        assert rv.status_code == 400
        assert b'Failed to decode JSON object' in rv.data

    def test_post_empty_json_wont_add_exception_to_response_if_no_debug(self):
        app = flask.Flask(__name__)
        app.config['DEBUG'] = False
        @app.route('/json', methods=['POST'])
        def post_json():
            flask.request.get_json()
            return None
        c = app.test_client()
        rv = c.post('/json', data=None, content_type='application/json')
        assert rv.status_code == 400
        assert b'Failed to decode JSON object' not in rv.data

    def test_json_bad_requests(self):
        app = flask.Flask(__name__)
        @app.route('/json', methods=['POST'])
        def return_json():
            return flask.jsonify(foo=text_type(flask.request.get_json()))
        c = app.test_client()
        rv = c.post('/json', data='malformed', content_type='application/json')
        assert rv.status_code == 400

    def test_json_custom_mimetypes(self):
        app = flask.Flask(__name__)
        @app.route('/json', methods=['POST'])
        def return_json():
            return flask.request.get_json()
        c = app.test_client()
        rv = c.post('/json', data='"foo"', content_type='application/x+json')
        assert rv.data == b'foo'

    def test_json_body_encoding(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            return flask.request.get_json()

        c = app.test_client()
        resp = c.get('/', data=u'"Hällo Wörld"'.encode('iso-8859-15'),
                     content_type='application/json; charset=iso-8859-15')
        assert resp.data == u'Hällo Wörld'.encode('utf-8')

    def test_json_as_unicode(self):
        app = flask.Flask(__name__)

        app.config['JSON_AS_ASCII'] = True
        with app.app_context():
            rv = flask.json.dumps(u'\N{SNOWMAN}')
            assert rv == '"\\u2603"'

        app.config['JSON_AS_ASCII'] = False
        with app.app_context():
            rv = flask.json.dumps(u'\N{SNOWMAN}')
            assert rv == u'"\u2603"'

    def test_json_dump_to_file(self):
        app = flask.Flask(__name__)
        test_data = {'name': 'Flask'}
        out = StringIO()

        with app.app_context():
            flask.json.dump(test_data, out)
            out.seek(0)
            rv = flask.json.load(out)
            assert rv == test_data

    @pytest.mark.parametrize('test_value', [0, -1, 1, 23, 3.14, 's', "longer string", True, False, None])
    def test_jsonify_basic_types(self, test_value):
        """Test jsonify with basic types."""
        app = flask.Flask(__name__)
        c = app.test_client()

        url = '/jsonify_basic_types'
        app.add_url_rule(url, url, lambda x=test_value: flask.jsonify(x))
        rv = c.get(url)
        assert rv.mimetype == 'application/json'
        assert flask.json.loads(rv.data) == test_value

    def test_jsonify_dicts(self):
        """Test jsonify with dicts and kwargs unpacking."""
        d = dict(
            a=0, b=23, c=3.14, d='t', e='Hi', f=True, g=False,
            h=['test list', 10, False],
            i={'test':'dict'}
        )
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

    def test_jsonify_arrays(self):
        """Test jsonify of lists and args unpacking."""
        l = [
            0, 42, 3.14, 't', 'hello', True, False,
            ['test list', 2, False],
            {'test':'dict'}
        ]
        app = flask.Flask(__name__)
        @app.route('/args_unpack')
        def return_args_unpack():
            return flask.jsonify(*l)
        @app.route('/array')
        def return_array():
            return flask.jsonify(l)
        c = app.test_client()
        for url in '/args_unpack', '/array':
            rv = c.get(url)
            assert rv.mimetype == 'application/json'
            assert flask.json.loads(rv.data) == l

    def test_jsonify_date_types(self):
        """Test jsonify with datetime.date and datetime.datetime types."""
        test_dates = (
            datetime.datetime(1973, 3, 11, 6, 30, 45),
            datetime.date(1975, 1, 5)
        )
        app = flask.Flask(__name__)
        c = app.test_client()

        for i, d in enumerate(test_dates):
            url = '/datetest{0}'.format(i)
            app.add_url_rule(url, str(i), lambda val=d: flask.jsonify(x=val))
            rv = c.get(url)
            assert rv.mimetype == 'application/json'
            assert flask.json.loads(rv.data)['x'] == http_date(d.timetuple())

    def test_jsonify_uuid_types(self):
        """Test jsonify with uuid.UUID types"""

        test_uuid = uuid.UUID(bytes=b'\xDE\xAD\xBE\xEF' * 4)
        app = flask.Flask(__name__)
        url = '/uuid_test'
        app.add_url_rule(url, url, lambda: flask.jsonify(x=test_uuid))

        c = app.test_client()
        rv = c.get(url)

        rv_x = flask.json.loads(rv.data)['x']
        assert rv_x == str(test_uuid)
        rv_uuid = uuid.UUID(rv_x)
        assert rv_uuid == test_uuid

    def test_json_attr(self):
        app = flask.Flask(__name__)
        @app.route('/add', methods=['POST'])
        def add():
            json = flask.request.get_json()
            return text_type(json['a'] + json['b'])
        c = app.test_client()
        rv = c.post('/add', data=flask.json.dumps({'a': 1, 'b': 2}),
                            content_type='application/json')
        assert rv.data == b'3'

    def test_template_escaping(self):
        app = flask.Flask(__name__)
        render = flask.render_template_string
        with app.test_request_context():
            rv = flask.json.htmlsafe_dumps('</script>')
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
            rv = render("<a ng-data='{{ data|tojson }}'></a>",
                data={'x': ["foo", "bar", "baz'"]})
            assert rv == '<a ng-data=\'{"x": ["foo", "bar", "baz\\u0027"]}\'></a>'

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
        assert rv.data == b'"<42>"'

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
        assert rv.status_code == 200
        assert rv.data == u'정상처리'.encode('utf-8')

    if not has_encoding('euc-kr'):
        test_modified_url_encoding = None

    def test_json_key_sorting(self):
        app = flask.Flask(__name__)
        app.testing = True
        assert app.config['JSON_SORT_KEYS'] == True
        d = dict.fromkeys(range(20), 'foo')

        @app.route('/')
        def index():
            return flask.jsonify(values=d)

        c = app.test_client()
        rv = c.get('/')
        lines = [x.strip() for x in rv.data.strip().decode('utf-8').splitlines()]
        sorted_by_str = [
            '{',
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
            '}',
            '}'
        ]
        sorted_by_int = [
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
        ]

        try:
            assert lines == sorted_by_int
        except AssertionError:
            assert lines == sorted_by_str

class TestSendfile(object):

    def test_send_file_regular(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            assert rv.direct_passthrough
            assert rv.mimetype == 'text/html'
            with app.open_resource('static/index.html') as f:
                rv.direct_passthrough = False
                assert rv.data == f.read()
            rv.close()

    def test_send_file_xsendfile(self, catch_deprecation_warnings):
        app = flask.Flask(__name__)
        app.use_x_sendfile = True
        with app.test_request_context():
            rv = flask.send_file('static/index.html')
            assert rv.direct_passthrough
            assert 'x-sendfile' in rv.headers
            assert rv.headers['x-sendfile'] == \
                os.path.join(app.root_path, 'static/index.html')
            assert rv.mimetype == 'text/html'
            rv.close()

    def test_send_file_last_modified(self):
        app = flask.Flask(__name__)
        last_modified = datetime.datetime(1999, 1, 1)

        @app.route('/')
        def index():
            return flask.send_file(StringIO("party like it's"),
                                   last_modified=last_modified,
                                   mimetype='text/plain')

        c = app.test_client()
        rv = c.get('/')
        assert rv.last_modified == last_modified

    def test_send_file_object_without_mimetype(self):
        app = flask.Flask(__name__)

        with app.test_request_context():
            with pytest.raises(ValueError) as excinfo:
                flask.send_file(StringIO("LOL"))
            assert 'Unable to infer MIME-type' in str(excinfo)
            assert 'no filename is available' in str(excinfo)

        with app.test_request_context():
            flask.send_file(StringIO("LOL"), attachment_filename='filename')

    def test_send_file_object(self):
        app = flask.Flask(__name__)

        with app.test_request_context():
            with open(os.path.join(app.root_path, 'static/index.html'), mode='rb') as f:
                rv = flask.send_file(f, mimetype='text/html')
                rv.direct_passthrough = False
                with app.open_resource('static/index.html') as f:
                    assert rv.data == f.read()
                assert rv.mimetype == 'text/html'
                rv.close()

        app.use_x_sendfile = True

        with app.test_request_context():
            with open(os.path.join(app.root_path, 'static/index.html')) as f:
                rv = flask.send_file(f, mimetype='text/html')
                assert rv.mimetype == 'text/html'
                assert 'x-sendfile' not in rv.headers
                rv.close()

        app.use_x_sendfile = False
        with app.test_request_context():
            f = StringIO('Test')
            rv = flask.send_file(f, mimetype='application/octet-stream')
            rv.direct_passthrough = False
            assert rv.data == b'Test'
            assert rv.mimetype == 'application/octet-stream'
            rv.close()

            class PyStringIO(object):
                def __init__(self, *args, **kwargs):
                    self._io = StringIO(*args, **kwargs)
                def __getattr__(self, name):
                    return getattr(self._io, name)
            f = PyStringIO('Test')
            f.name = 'test.txt'
            rv = flask.send_file(f, attachment_filename=f.name)
            rv.direct_passthrough = False
            assert rv.data == b'Test'
            assert rv.mimetype == 'text/plain'
            rv.close()

            f = StringIO('Test')
            rv = flask.send_file(f, mimetype='text/plain')
            rv.direct_passthrough = False
            assert rv.data == b'Test'
            assert rv.mimetype == 'text/plain'
            rv.close()

        app.use_x_sendfile = True

        with app.test_request_context():
            f = StringIO('Test')
            rv = flask.send_file(f, mimetype='text/html')
            assert 'x-sendfile' not in rv.headers
            rv.close()

    @pytest.mark.skipif(
        not callable(getattr(Range, 'to_content_range_header', None)),
        reason="not implement within werkzeug"
    )
    def test_send_file_range_request(self):
        app = flask.Flask(__name__)

        @app.route('/')
        def index():
            return flask.send_file('static/index.html', conditional=True)

        c = app.test_client()

        rv = c.get('/', headers={'Range': 'bytes=4-15'})
        assert rv.status_code == 206
        with app.open_resource('static/index.html') as f:
            assert rv.data == f.read()[4:16]
        rv.close()

        rv = c.get('/', headers={'Range': 'bytes=4-'})
        assert rv.status_code == 206
        with app.open_resource('static/index.html') as f:
            assert rv.data == f.read()[4:]
        rv.close()

        rv = c.get('/', headers={'Range': 'bytes=4-1000'})
        assert rv.status_code == 206
        with app.open_resource('static/index.html') as f:
            assert rv.data == f.read()[4:]
        rv.close()

        rv = c.get('/', headers={'Range': 'bytes=-10'})
        assert rv.status_code == 206
        with app.open_resource('static/index.html') as f:
            assert rv.data == f.read()[-10:]
        rv.close()

        rv = c.get('/', headers={'Range': 'bytes=1000-'})
        assert rv.status_code == 416
        rv.close()

        rv = c.get('/', headers={'Range': 'bytes=-'})
        assert rv.status_code == 416
        rv.close()

        rv = c.get('/', headers={'Range': 'somethingsomething'})
        assert rv.status_code == 416
        rv.close()

        last_modified = datetime.datetime.fromtimestamp(os.path.getmtime(
            os.path.join(app.root_path, 'static/index.html'))).replace(
            microsecond=0)

        rv = c.get('/', headers={'Range': 'bytes=4-15',
                                 'If-Range': http_date(last_modified)})
        assert rv.status_code == 206
        rv.close()

        rv = c.get('/', headers={'Range': 'bytes=4-15', 'If-Range': http_date(
            datetime.datetime(1999, 1, 1))})
        assert rv.status_code == 200
        rv.close()

    def test_attachment(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            with open(os.path.join(app.root_path, 'static/index.html')) as f:
                rv = flask.send_file(f, as_attachment=True,
                                     attachment_filename='index.html')
                value, options = \
                    parse_options_header(rv.headers['Content-Disposition'])
                assert value == 'attachment'
                rv.close()

        with app.test_request_context():
            assert options['filename'] == 'index.html'
            rv = flask.send_file('static/index.html', as_attachment=True)
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            assert value == 'attachment'
            assert options['filename'] == 'index.html'
            rv.close()

        with app.test_request_context():
            rv = flask.send_file(StringIO('Test'), as_attachment=True,
                                 attachment_filename='index.txt',
                                 add_etags=False)
            assert rv.mimetype == 'text/plain'
            value, options = parse_options_header(rv.headers['Content-Disposition'])
            assert value == 'attachment'
            assert options['filename'] == 'index.txt'
            rv.close()

    def test_static_file(self):
        app = flask.Flask(__name__)
        # default cache timeout is 12 hours
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            assert cc.max_age == 12 * 60 * 60
            rv.close()
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            assert cc.max_age == 12 * 60 * 60
            rv.close()
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = 3600
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            assert cc.max_age == 3600
            rv.close()
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            assert cc.max_age == 3600
            rv.close()
        class StaticFileApp(flask.Flask):
            def get_send_file_max_age(self, filename):
                return 10
        app = StaticFileApp(__name__)
        with app.test_request_context():
            # Test with static file handler.
            rv = app.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            assert cc.max_age == 10
            rv.close()
            # Test again with direct use of send_file utility.
            rv = flask.send_file('static/index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            assert cc.max_age == 10
            rv.close()

    def test_send_from_directory(self):
        app = flask.Flask(__name__)
        app.testing = True
        app.root_path = os.path.join(os.path.dirname(__file__),
                                     'test_apps', 'subdomaintestmodule')
        with app.test_request_context():
            rv = flask.send_from_directory('static', 'hello.txt')
            rv.direct_passthrough = False
            assert rv.data.strip() == b'Hello Subdomain'
            rv.close()

    def test_send_from_directory_bad_request(self):
        app = flask.Flask(__name__)
        app.testing = True
        app.root_path = os.path.join(os.path.dirname(__file__),
                                     'test_apps', 'subdomaintestmodule')
        with app.test_request_context():
            with pytest.raises(BadRequest):
                flask.send_from_directory('static', 'bad\x00')

class TestLogging(object):

    def test_logger_cache(self):
        app = flask.Flask(__name__)
        logger1 = app.logger
        assert app.logger is logger1
        assert logger1.name == __name__
        app.logger_name = __name__ + '/test_logger_cache'
        assert app.logger is not logger1

    def test_debug_log(self, capsys):
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
            c.get('/')
            out, err = capsys.readouterr()
            assert 'WARNING in test_helpers [' in err
            assert os.path.basename(__file__.rsplit('.', 1)[0] + '.py') in err
            assert 'the standard library is dead' in err
            assert 'this is a debug statement' in err

            with pytest.raises(ZeroDivisionError):
                c.get('/exc')

    def test_debug_log_override(self):
        app = flask.Flask(__name__)
        app.debug = True
        app.logger_name = 'flask_tests/test_debug_log_override'
        app.logger.level = 10
        assert app.logger.level == 10

    def test_exception_logging(self):
        out = StringIO()
        app = flask.Flask(__name__)
        app.config['LOGGER_HANDLER_POLICY'] = 'never'
        app.logger_name = 'flask_tests/test_exception_logging'
        app.logger.addHandler(StreamHandler(out))

        @app.route('/')
        def index():
            1 // 0

        rv = app.test_client().get('/')
        assert rv.status_code == 500
        assert b'Internal Server Error' in rv.data

        err = out.getvalue()
        assert 'Exception on / [GET]' in err
        assert 'Traceback (most recent call last):' in err
        assert '1 // 0' in err
        assert 'ZeroDivisionError:' in err

    def test_processor_exceptions(self):
        app = flask.Flask(__name__)
        app.config['LOGGER_HANDLER_POLICY'] = 'never'
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
            assert rv.status_code == 500
            assert rv.data == b'Hello Server Error'

    def test_url_for_with_anchor(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            assert flask.url_for('index', _anchor='x y') == '/#x%20y'

    def test_url_for_with_scheme(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            assert flask.url_for('index', _external=True, _scheme='https') == 'https://localhost/'

    def test_url_for_with_scheme_not_external(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            pytest.raises(ValueError,
                               flask.url_for,
                               'index',
                               _scheme='https')

    def test_url_for_with_alternating_schemes(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return '42'
        with app.test_request_context():
            assert flask.url_for('index', _external=True) == 'http://localhost/'
            assert flask.url_for('index', _external=True, _scheme='https') == 'https://localhost/'
            assert flask.url_for('index', _external=True) == 'http://localhost/'

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
            assert flask.url_for('myview', _method='GET') == '/myview/'
            assert flask.url_for('myview', id=42, _method='GET') == '/myview/42'
            assert flask.url_for('myview', _method='POST') == '/myview/create'


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
        modules_tmpdir.join('importerror.py').write('raise NotImplementedError()')
        try:
            flask.Flask('importerror')
        except NotImplementedError:
            assert False, 'Flask(import_name) is importing import_name.'


class TestStreaming(object):

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
        assert rv.data == b'Hello World!'

    def test_streaming_with_context_as_decorator(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            @flask.stream_with_context
            def generate(hello):
                yield hello
                yield flask.request.args['name']
                yield '!'
            return flask.Response(generate('Hello '))
        c = app.test_client()
        rv = c.get('/?name=World')
        assert rv.data == b'Hello World!'

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
        assert rv.data == b'Hello World!'
        assert called == [42]


class TestSafeJoin(object):

    def test_safe_join(self):
        # Valid combinations of *args and expected joined paths.
        passing = (
            (('a/b/c', ), 'a/b/c'),
            (('/', 'a/', 'b/', 'c/', ), '/a/b/c'),
            (('a', 'b', 'c', ), 'a/b/c'),
            (('/a', 'b/c', ), '/a/b/c'),
            (('a/b', 'X/../c'), 'a/b/c', ),
            (('/a/b', 'c/X/..'), '/a/b/c', ),
            # If last path is '' add a slash
            (('/a/b/c', '', ), '/a/b/c/', ),
            # Preserve dot slash
            (('/a/b/c', './', ), '/a/b/c/.', ),
            (('a/b/c', 'X/..'), 'a/b/c/.', ),
            # Base directory is always considered safe
            (('../', 'a/b/c'), '../a/b/c'),
            (('/..', ), '/..'),
        )

        for args, expected in passing:
            assert flask.safe_join(*args) == expected

    def test_safe_join_exceptions(self):
        # Should raise werkzeug.exceptions.NotFound on unsafe joins.
        failing = (
            # path.isabs and ``..'' checks
            ('/a', 'b', '/c'),
            ('/a', '../b/c', ),
            ('/a', '..', 'b/c'),
            # Boundaries violations after path normalization
            ('/a', 'b/../b/../../c', ),
            ('/a', 'b', 'c/../..'),
            ('/a', 'b/../../c', ),
        )

        for args in failing:
            with pytest.raises(NotFound):
                print(flask.safe_join(*args))
