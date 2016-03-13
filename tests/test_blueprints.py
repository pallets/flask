# -*- coding: utf-8 -*-
"""
    tests.blueprints
    ~~~~~~~~~~~~~~~~

    Blueprints (and currently modules)

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import flask

from flask._compat import text_type
from werkzeug.http import parse_cache_control_header
from jinja2 import TemplateNotFound


def test_blueprint_specific_error_handling():
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

    assert c.get('/frontend-no').data == b'frontend says no'
    assert c.get('/backend-no').data == b'backend says no'
    assert c.get('/what-is-a-sideend').data == b'application itself says no'

def test_blueprint_specific_user_error_handling():
    class MyDecoratorException(Exception):
        pass
    class MyFunctionException(Exception):
        pass

    blue = flask.Blueprint('blue', __name__)

    @blue.errorhandler(MyDecoratorException)
    def my_decorator_exception_handler(e):
        assert isinstance(e, MyDecoratorException)
        return 'boom'

    def my_function_exception_handler(e):
        assert isinstance(e, MyFunctionException)
        return 'bam'
    blue.register_error_handler(MyFunctionException, my_function_exception_handler)

    @blue.route('/decorator')
    def blue_deco_test():
        raise MyDecoratorException()
    @blue.route('/function')
    def blue_func_test():
        raise MyFunctionException()

    app = flask.Flask(__name__)
    app.register_blueprint(blue)

    c = app.test_client()

    assert c.get('/decorator').data == b'boom'
    assert c.get('/function').data == b'bam'

def test_blueprint_url_definitions():
    bp = flask.Blueprint('test', __name__)

    @bp.route('/foo', defaults={'baz': 42})
    def foo(bar, baz):
        return '%s/%d' % (bar, baz)

    @bp.route('/bar')
    def bar(bar):
        return text_type(bar)

    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/1', url_defaults={'bar': 23})
    app.register_blueprint(bp, url_prefix='/2', url_defaults={'bar': 19})

    c = app.test_client()
    assert c.get('/1/foo').data == b'23/42'
    assert c.get('/2/foo').data == b'19/42'
    assert c.get('/1/bar').data == b'23'
    assert c.get('/2/bar').data == b'19'

def test_blueprint_url_processors():
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

    assert c.get('/de/').data == b'/de/about'
    assert c.get('/de/about').data == b'/de/'

def test_templates_and_static(test_apps):
    from blueprintapp import app
    c = app.test_client()

    rv = c.get('/')
    assert rv.data == b'Hello from the Frontend'
    rv = c.get('/admin/')
    assert rv.data == b'Hello from the Admin'
    rv = c.get('/admin/index2')
    assert rv.data == b'Hello from the Admin'
    rv = c.get('/admin/static/test.txt')
    assert rv.data.strip() == b'Admin File'
    rv.close()
    rv = c.get('/admin/static/css/test.css')
    assert rv.data.strip() == b'/* nested file */'
    rv.close()

    # try/finally, in case other tests use this app for Blueprint tests.
    max_age_default = app.config['SEND_FILE_MAX_AGE_DEFAULT']
    try:
        expected_max_age = 3600
        if app.config['SEND_FILE_MAX_AGE_DEFAULT'] == expected_max_age:
            expected_max_age = 7200
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = expected_max_age
        rv = c.get('/admin/static/css/test.css')
        cc = parse_cache_control_header(rv.headers['Cache-Control'])
        assert cc.max_age == expected_max_age
        rv.close()
    finally:
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = max_age_default

    with app.test_request_context():
        assert flask.url_for('admin.static', filename='test.txt') == '/admin/static/test.txt'

    with app.test_request_context():
        with pytest.raises(TemplateNotFound) as e:
            flask.render_template('missing.html')
        assert e.value.name == 'missing.html'

    with flask.Flask(__name__).test_request_context():
        assert flask.render_template('nested/nested.txt') == 'I\'m nested'

def test_default_static_cache_timeout():
    app = flask.Flask(__name__)
    class MyBlueprint(flask.Blueprint):
        def get_send_file_max_age(self, filename):
            return 100

    blueprint = MyBlueprint('blueprint', __name__, static_folder='static')
    app.register_blueprint(blueprint)

    # try/finally, in case other tests use this app for Blueprint tests.
    max_age_default = app.config['SEND_FILE_MAX_AGE_DEFAULT']
    try:
        with app.test_request_context():
            unexpected_max_age = 3600
            if app.config['SEND_FILE_MAX_AGE_DEFAULT'] == unexpected_max_age:
                unexpected_max_age = 7200
            app.config['SEND_FILE_MAX_AGE_DEFAULT'] = unexpected_max_age
            rv = blueprint.send_static_file('index.html')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            assert cc.max_age == 100
            rv.close()
    finally:
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = max_age_default

def test_templates_list(test_apps):
    from blueprintapp import app
    templates = sorted(app.jinja_env.list_templates())
    assert templates == ['admin/index.html', 'frontend/index.html']

def test_dotted_names():
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
    assert c.get('/fe').data.strip() == b'/be'
    assert c.get('/fe2').data.strip() == b'/fe'
    assert c.get('/be').data.strip() == b'/fe'

def test_dotted_names_from_app():
    app = flask.Flask(__name__)
    app.testing = True
    test = flask.Blueprint('test', __name__)

    @app.route('/')
    def app_index():
        return flask.url_for('test.index')

    @test.route('/test/')
    def index():
        return flask.url_for('app_index')

    app.register_blueprint(test)

    with app.test_client() as c:
        rv = c.get('/')
        assert rv.data == b'/test/'

def test_empty_url_defaults():
    bp = flask.Blueprint('bp', __name__)

    @bp.route('/', defaults={'page': 1})
    @bp.route('/page/<int:page>')
    def something(page):
        return str(page)

    app = flask.Flask(__name__)
    app.register_blueprint(bp)

    c = app.test_client()
    assert c.get('/').data == b'1'
    assert c.get('/page/2').data == b'2'

def test_route_decorator_custom_endpoint():

    bp = flask.Blueprint('bp', __name__)

    @bp.route('/foo')
    def foo():
        return flask.request.endpoint

    @bp.route('/bar', endpoint='bar')
    def foo_bar():
        return flask.request.endpoint

    @bp.route('/bar/123', endpoint='123')
    def foo_bar_foo():
        return flask.request.endpoint

    @bp.route('/bar/foo')
    def bar_foo():
        return flask.request.endpoint

    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.request.endpoint

    c = app.test_client()
    assert c.get('/').data == b'index'
    assert c.get('/py/foo').data == b'bp.foo'
    assert c.get('/py/bar').data == b'bp.bar'
    assert c.get('/py/bar/123').data == b'bp.123'
    assert c.get('/py/bar/foo').data == b'bp.bar_foo'

def test_route_decorator_custom_endpoint_with_dots():
    bp = flask.Blueprint('bp', __name__)

    @bp.route('/foo')
    def foo():
        return flask.request.endpoint

    try:
        @bp.route('/bar', endpoint='bar.bar')
        def foo_bar():
            return flask.request.endpoint
    except AssertionError:
        pass
    else:
        raise AssertionError('expected AssertionError not raised')

    try:
        @bp.route('/bar/123', endpoint='bar.123')
        def foo_bar_foo():
            return flask.request.endpoint
    except AssertionError:
        pass
    else:
        raise AssertionError('expected AssertionError not raised')

    def foo_foo_foo():
        pass

    pytest.raises(
        AssertionError,
        lambda: bp.add_url_rule(
            '/bar/123', endpoint='bar.123', view_func=foo_foo_foo
        )
    )

    pytest.raises(
        AssertionError,
        bp.route('/bar/123', endpoint='bar.123'),
        lambda: None
    )

    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')

    c = app.test_client()
    assert c.get('/py/foo').data == b'bp.foo'
    # The rule's didn't actually made it through
    rv = c.get('/py/bar')
    assert rv.status_code == 404
    rv = c.get('/py/bar/123')
    assert rv.status_code == 404

def test_template_filter():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_filter()
    def my_reverse(s):
        return s[::-1]
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'my_reverse' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['my_reverse'] == my_reverse
    assert app.jinja_env.filters['my_reverse']('abcd') == 'dcba'

def test_add_template_filter():
    bp = flask.Blueprint('bp', __name__)
    def my_reverse(s):
        return s[::-1]
    bp.add_app_template_filter(my_reverse)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'my_reverse' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['my_reverse'] == my_reverse
    assert app.jinja_env.filters['my_reverse']('abcd') == 'dcba'

def test_template_filter_with_name():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_filter('strrev')
    def my_reverse(s):
        return s[::-1]
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'strrev' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['strrev'] == my_reverse
    assert app.jinja_env.filters['strrev']('abcd') == 'dcba'

def test_add_template_filter_with_name():
    bp = flask.Blueprint('bp', __name__)
    def my_reverse(s):
        return s[::-1]
    bp.add_app_template_filter(my_reverse, 'strrev')
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'strrev' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['strrev'] == my_reverse
    assert app.jinja_env.filters['strrev']('abcd') == 'dcba'

def test_template_filter_with_template():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_filter()
    def super_reverse(s):
        return s[::-1]
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_template_filter_after_route_with_template():
    app = flask.Flask(__name__)
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_filter()
    def super_reverse(s):
        return s[::-1]
    app.register_blueprint(bp, url_prefix='/py')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_add_template_filter_with_template():
    bp = flask.Blueprint('bp', __name__)
    def super_reverse(s):
        return s[::-1]
    bp.add_app_template_filter(super_reverse)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_template_filter_with_name_and_template():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_filter('super_reverse')
    def my_reverse(s):
        return s[::-1]
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_add_template_filter_with_name_and_template():
    bp = flask.Blueprint('bp', __name__)
    def my_reverse(s):
        return s[::-1]
    bp.add_app_template_filter(my_reverse, 'super_reverse')
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')
    rv = app.test_client().get('/')
    assert rv.data == b'dcba'

def test_template_test():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_test()
    def is_boolean(value):
        return isinstance(value, bool)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'is_boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['is_boolean'] == is_boolean
    assert app.jinja_env.tests['is_boolean'](False)

def test_add_template_test():
    bp = flask.Blueprint('bp', __name__)
    def is_boolean(value):
        return isinstance(value, bool)
    bp.add_app_template_test(is_boolean)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'is_boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['is_boolean'] == is_boolean
    assert app.jinja_env.tests['is_boolean'](False)

def test_template_test_with_name():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_test('boolean')
    def is_boolean(value):
        return isinstance(value, bool)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == is_boolean
    assert app.jinja_env.tests['boolean'](False)

def test_add_template_test_with_name():
    bp = flask.Blueprint('bp', __name__)
    def is_boolean(value):
        return isinstance(value, bool)
    bp.add_app_template_test(is_boolean, 'boolean')
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == is_boolean
    assert app.jinja_env.tests['boolean'](False)

def test_template_test_with_template():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_test()
    def boolean(value):
        return isinstance(value, bool)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_template_test_after_route_with_template():
    app = flask.Flask(__name__)
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_test()
    def boolean(value):
        return isinstance(value, bool)
    app.register_blueprint(bp, url_prefix='/py')
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_add_template_test_with_template():
    bp = flask.Blueprint('bp', __name__)
    def boolean(value):
        return isinstance(value, bool)
    bp.add_app_template_test(boolean)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_template_test_with_name_and_template():
    bp = flask.Blueprint('bp', __name__)
    @bp.app_template_test('boolean')
    def is_boolean(value):
        return isinstance(value, bool)
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data

def test_add_template_test_with_name_and_template():
    bp = flask.Blueprint('bp', __name__)
    def is_boolean(value):
        return isinstance(value, bool)
    bp.add_app_template_test(is_boolean, 'boolean')
    app = flask.Flask(__name__)
    app.register_blueprint(bp, url_prefix='/py')
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)
    rv = app.test_client().get('/')
    assert b'Success!' in rv.data
