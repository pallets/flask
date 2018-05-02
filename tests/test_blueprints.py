# -*- coding: utf-8 -*-
"""
    tests.blueprints
    ~~~~~~~~~~~~~~~~

    Blueprints (and currently modules)

    :copyright: © 2010 by the Pallets team.
    :license: BSD, see LICENSE for more details.
"""

import functools
import pytest

import flask

from flask._compat import text_type
from werkzeug.http import parse_cache_control_header
from jinja2 import TemplateNotFound


def test_blueprint_specific_error_handling(app, client):
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

    app.register_blueprint(frontend)
    app.register_blueprint(backend)
    app.register_blueprint(sideend)

    @app.errorhandler(403)
    def app_forbidden(e):
        return 'application itself says no', 403

    assert client.get('/frontend-no').data == b'frontend says no'
    assert client.get('/backend-no').data == b'backend says no'
    assert client.get('/what-is-a-sideend').data == b'application itself says no'


def test_blueprint_specific_user_error_handling(app, client):
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

    app.register_blueprint(blue)

    assert client.get('/decorator').data == b'boom'
    assert client.get('/function').data == b'bam'


def test_blueprint_app_error_handling(app, client):
    errors = flask.Blueprint('errors', __name__)

    @errors.app_errorhandler(403)
    def forbidden_handler(e):
        return 'you shall not pass', 403

    @app.route('/forbidden')
    def app_forbidden():
        flask.abort(403)

    forbidden_bp = flask.Blueprint('forbidden_bp', __name__)

    @forbidden_bp.route('/nope')
    def bp_forbidden():
        flask.abort(403)

    app.register_blueprint(errors)
    app.register_blueprint(forbidden_bp)

    assert client.get('/forbidden').data == b'you shall not pass'
    assert client.get('/nope').data == b'you shall not pass'


@pytest.mark.parametrize(('prefix', 'rule', 'url'), (
    ('', '/', '/'),
    ('/', '', '/'),
    ('/', '/', '/'),
    ('/foo', '', '/foo'),
    ('/foo/', '', '/foo/'),
    ('', '/bar', '/bar'),
    ('/foo/', '/bar', '/foo/bar'),
    ('/foo/', 'bar', '/foo/bar'),
    ('/foo', '/bar', '/foo/bar'),
    ('/foo/', '//bar', '/foo/bar'),
    ('/foo//', '/bar', '/foo/bar'),
))
def test_blueprint_prefix_slash(app, client, prefix, rule, url):
    bp = flask.Blueprint('test', __name__, url_prefix=prefix)

    @bp.route(rule)
    def index():
        return '', 204

    app.register_blueprint(bp)
    assert client.get(url).status_code == 204


def test_blueprint_url_defaults(app, client):
    bp = flask.Blueprint('test', __name__)

    @bp.route('/foo', defaults={'baz': 42})
    def foo(bar, baz):
        return '%s/%d' % (bar, baz)

    @bp.route('/bar')
    def bar(bar):
        return text_type(bar)

    app.register_blueprint(bp, url_prefix='/1', url_defaults={'bar': 23})
    app.register_blueprint(bp, url_prefix='/2', url_defaults={'bar': 19})

    assert client.get('/1/foo').data == b'23/42'
    assert client.get('/2/foo').data == b'19/42'
    assert client.get('/1/bar').data == b'23'
    assert client.get('/2/bar').data == b'19'


def test_blueprint_url_processors(app, client):
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

    app.register_blueprint(bp)

    assert client.get('/de/').data == b'/de/about'
    assert client.get('/de/about').data == b'/de/'


def test_templates_and_static(test_apps):
    from blueprintapp import app
    client = app.test_client()

    rv = client.get('/')
    assert rv.data == b'Hello from the Frontend'
    rv = client.get('/admin/')
    assert rv.data == b'Hello from the Admin'
    rv = client.get('/admin/index2')
    assert rv.data == b'Hello from the Admin'
    rv = client.get('/admin/static/test.txt')
    assert rv.data.strip() == b'Admin File'
    rv.close()
    rv = client.get('/admin/static/css/test.css')
    assert rv.data.strip() == b'/* nested file */'
    rv.close()

    # try/finally, in case other tests use this app for Blueprint tests.
    max_age_default = app.config['SEND_FILE_MAX_AGE_DEFAULT']
    try:
        expected_max_age = 3600
        if app.config['SEND_FILE_MAX_AGE_DEFAULT'] == expected_max_age:
            expected_max_age = 7200
        app.config['SEND_FILE_MAX_AGE_DEFAULT'] = expected_max_age
        rv = client.get('/admin/static/css/test.css')
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


def test_default_static_cache_timeout(app):
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


def test_dotted_names(app, client):
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

    app.register_blueprint(frontend)
    app.register_blueprint(backend)

    assert client.get('/fe').data.strip() == b'/be'
    assert client.get('/fe2').data.strip() == b'/fe'
    assert client.get('/be').data.strip() == b'/fe'


def test_dotted_names_from_app(app, client):
    test = flask.Blueprint('test', __name__)

    @app.route('/')
    def app_index():
        return flask.url_for('test.index')

    @test.route('/test/')
    def index():
        return flask.url_for('app_index')

    app.register_blueprint(test)

    rv = client.get('/')
    assert rv.data == b'/test/'


def test_empty_url_defaults(app, client):
    bp = flask.Blueprint('bp', __name__)

    @bp.route('/', defaults={'page': 1})
    @bp.route('/page/<int:page>')
    def something(page):
        return str(page)

    app.register_blueprint(bp)

    assert client.get('/').data == b'1'
    assert client.get('/page/2').data == b'2'


def test_route_decorator_custom_endpoint(app, client):
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

    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.request.endpoint

    assert client.get('/').data == b'index'
    assert client.get('/py/foo').data == b'bp.foo'
    assert client.get('/py/bar').data == b'bp.bar'
    assert client.get('/py/bar/123').data == b'bp.123'
    assert client.get('/py/bar/foo').data == b'bp.bar_foo'


def test_route_decorator_custom_endpoint_with_dots(app, client):
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

    foo_foo_foo.__name__ = 'bar.123'

    pytest.raises(
        AssertionError,
        lambda: bp.add_url_rule(
            '/bar/123', view_func=foo_foo_foo
        )
    )

    bp.add_url_rule('/bar/456', endpoint='foofoofoo', view_func=functools.partial(foo_foo_foo))

    app.register_blueprint(bp, url_prefix='/py')

    assert client.get('/py/foo').data == b'bp.foo'
    # The rule's didn't actually made it through
    rv = client.get('/py/bar')
    assert rv.status_code == 404
    rv = client.get('/py/bar/123')
    assert rv.status_code == 404


def test_endpoint_decorator(app, client):
    from werkzeug.routing import Rule
    app.url_map.add(Rule('/foo', endpoint='bar'))

    bp = flask.Blueprint('bp', __name__)

    @bp.endpoint('bar')
    def foobar():
        return flask.request.endpoint

    app.register_blueprint(bp, url_prefix='/bp_prefix')

    assert client.get('/foo').data == b'bar'
    assert client.get('/bp_prefix/bar').status_code == 404


def test_template_filter(app):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_filter()
    def my_reverse(s):
        return s[::-1]

    app.register_blueprint(bp, url_prefix='/py')
    assert 'my_reverse' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['my_reverse'] == my_reverse
    assert app.jinja_env.filters['my_reverse']('abcd') == 'dcba'


def test_add_template_filter(app):
    bp = flask.Blueprint('bp', __name__)

    def my_reverse(s):
        return s[::-1]

    bp.add_app_template_filter(my_reverse)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'my_reverse' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['my_reverse'] == my_reverse
    assert app.jinja_env.filters['my_reverse']('abcd') == 'dcba'


def test_template_filter_with_name(app):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_filter('strrev')
    def my_reverse(s):
        return s[::-1]

    app.register_blueprint(bp, url_prefix='/py')
    assert 'strrev' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['strrev'] == my_reverse
    assert app.jinja_env.filters['strrev']('abcd') == 'dcba'


def test_add_template_filter_with_name(app):
    bp = flask.Blueprint('bp', __name__)

    def my_reverse(s):
        return s[::-1]

    bp.add_app_template_filter(my_reverse, 'strrev')
    app.register_blueprint(bp, url_prefix='/py')
    assert 'strrev' in app.jinja_env.filters.keys()
    assert app.jinja_env.filters['strrev'] == my_reverse
    assert app.jinja_env.filters['strrev']('abcd') == 'dcba'


def test_template_filter_with_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_filter()
    def super_reverse(s):
        return s[::-1]

    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')

    rv = client.get('/')
    assert rv.data == b'dcba'


def test_template_filter_after_route_with_template(app, client):
    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')

    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_filter()
    def super_reverse(s):
        return s[::-1]

    app.register_blueprint(bp, url_prefix='/py')
    rv = client.get('/')
    assert rv.data == b'dcba'


def test_add_template_filter_with_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    def super_reverse(s):
        return s[::-1]

    bp.add_app_template_filter(super_reverse)
    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')

    rv = client.get('/')
    assert rv.data == b'dcba'


def test_template_filter_with_name_and_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_filter('super_reverse')
    def my_reverse(s):
        return s[::-1]

    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')

    rv = client.get('/')
    assert rv.data == b'dcba'


def test_add_template_filter_with_name_and_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    def my_reverse(s):
        return s[::-1]

    bp.add_app_template_filter(my_reverse, 'super_reverse')
    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_filter.html', value='abcd')

    rv = client.get('/')
    assert rv.data == b'dcba'


def test_template_test(app):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_test()
    def is_boolean(value):
        return isinstance(value, bool)

    app.register_blueprint(bp, url_prefix='/py')
    assert 'is_boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['is_boolean'] == is_boolean
    assert app.jinja_env.tests['is_boolean'](False)


def test_add_template_test(app):
    bp = flask.Blueprint('bp', __name__)

    def is_boolean(value):
        return isinstance(value, bool)

    bp.add_app_template_test(is_boolean)
    app.register_blueprint(bp, url_prefix='/py')
    assert 'is_boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['is_boolean'] == is_boolean
    assert app.jinja_env.tests['is_boolean'](False)


def test_template_test_with_name(app):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_test('boolean')
    def is_boolean(value):
        return isinstance(value, bool)

    app.register_blueprint(bp, url_prefix='/py')
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == is_boolean
    assert app.jinja_env.tests['boolean'](False)


def test_add_template_test_with_name(app):
    bp = flask.Blueprint('bp', __name__)

    def is_boolean(value):
        return isinstance(value, bool)

    bp.add_app_template_test(is_boolean, 'boolean')
    app.register_blueprint(bp, url_prefix='/py')
    assert 'boolean' in app.jinja_env.tests.keys()
    assert app.jinja_env.tests['boolean'] == is_boolean
    assert app.jinja_env.tests['boolean'](False)


def test_template_test_with_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_test()
    def boolean(value):
        return isinstance(value, bool)

    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)

    rv = client.get('/')
    assert b'Success!' in rv.data


def test_template_test_after_route_with_template(app, client):
    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)

    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_test()
    def boolean(value):
        return isinstance(value, bool)

    app.register_blueprint(bp, url_prefix='/py')
    rv = client.get('/')
    assert b'Success!' in rv.data


def test_add_template_test_with_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    def boolean(value):
        return isinstance(value, bool)

    bp.add_app_template_test(boolean)
    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)

    rv = client.get('/')
    assert b'Success!' in rv.data


def test_template_test_with_name_and_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_test('boolean')
    def is_boolean(value):
        return isinstance(value, bool)

    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)

    rv = client.get('/')
    assert b'Success!' in rv.data


def test_add_template_test_with_name_and_template(app, client):
    bp = flask.Blueprint('bp', __name__)

    def is_boolean(value):
        return isinstance(value, bool)

    bp.add_app_template_test(is_boolean, 'boolean')
    app.register_blueprint(bp, url_prefix='/py')

    @app.route('/')
    def index():
        return flask.render_template('template_test.html', value=False)

    rv = client.get('/')
    assert b'Success!' in rv.data


def test_context_processing(app, client):
    answer_bp = flask.Blueprint('answer_bp', __name__)

    template_string = lambda: flask.render_template_string(
        '{% if notanswer %}{{ notanswer }} is not the answer. {% endif %}'
        '{% if answer %}{{ answer }} is the answer.{% endif %}'
    )

    # App global context processor
    @answer_bp.app_context_processor
    def not_answer_context_processor():
        return {'notanswer': 43}

    # Blueprint local context processor
    @answer_bp.context_processor
    def answer_context_processor():
        return {'answer': 42}

    # Setup endpoints for testing
    @answer_bp.route('/bp')
    def bp_page():
        return template_string()

    @app.route('/')
    def app_page():
        return template_string()

    # Register the blueprint
    app.register_blueprint(answer_bp)

    app_page_bytes = client.get('/').data
    answer_page_bytes = client.get('/bp').data

    assert b'43' in app_page_bytes
    assert b'42' not in app_page_bytes

    assert b'42' in answer_page_bytes
    assert b'43' in answer_page_bytes


def test_template_global(app):
    bp = flask.Blueprint('bp', __name__)

    @bp.app_template_global()
    def get_answer():
        return 42

    # Make sure the function is not in the jinja_env already
    assert 'get_answer' not in app.jinja_env.globals.keys()
    app.register_blueprint(bp)

    # Tests
    assert 'get_answer' in app.jinja_env.globals.keys()
    assert app.jinja_env.globals['get_answer'] is get_answer
    assert app.jinja_env.globals['get_answer']() == 42

    with app.app_context():
        rv = flask.render_template_string('{{ get_answer() }}')
        assert rv == '42'


def test_request_processing(app, client):
    bp = flask.Blueprint('bp', __name__)
    evts = []

    @bp.before_request
    def before_bp():
        evts.append('before')

    @bp.after_request
    def after_bp(response):
        response.data += b'|after'
        evts.append('after')
        return response

    @bp.teardown_request
    def teardown_bp(exc):
        evts.append('teardown')

    # Setup routes for testing
    @bp.route('/bp')
    def bp_endpoint():
        return 'request'

    app.register_blueprint(bp)

    assert evts == []
    rv = client.get('/bp')
    assert rv.data == b'request|after'
    assert evts == ['before', 'after', 'teardown']


def test_app_request_processing(app, client):
    bp = flask.Blueprint('bp', __name__)
    evts = []

    @bp.before_app_first_request
    def before_first_request():
        evts.append('first')

    @bp.before_app_request
    def before_app():
        evts.append('before')

    @bp.after_app_request
    def after_app(response):
        response.data += b'|after'
        evts.append('after')
        return response

    @bp.teardown_app_request
    def teardown_app(exc):
        evts.append('teardown')

    app.register_blueprint(bp)

    # Setup routes for testing
    @app.route('/')
    def bp_endpoint():
        return 'request'

    # before first request
    assert evts == []

    # first request
    resp = client.get('/').data
    assert resp == b'request|after'
    assert evts == ['first', 'before', 'after', 'teardown']

    # second request
    resp = client.get('/').data
    assert resp == b'request|after'
    assert evts == ['first'] + ['before', 'after', 'teardown'] * 2


def test_app_url_processors(app, client):
    bp = flask.Blueprint('bp', __name__)

    # Register app-wide url defaults and preprocessor on blueprint
    @bp.app_url_defaults
    def add_language_code(endpoint, values):
        values.setdefault('lang_code', flask.g.lang_code)

    @bp.app_url_value_preprocessor
    def pull_lang_code(endpoint, values):
        flask.g.lang_code = values.pop('lang_code')

    # Register route rules at the app level
    @app.route('/<lang_code>/')
    def index():
        return flask.url_for('about')

    @app.route('/<lang_code>/about')
    def about():
        return flask.url_for('index')

    app.register_blueprint(bp)

    assert client.get('/de/').data == b'/de/about'
    assert client.get('/de/about').data == b'/de/'
