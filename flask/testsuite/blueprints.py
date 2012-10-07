# -*- coding: utf-8 -*-
"""
    flask.testsuite.blueprints
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Blueprints (and currently modules)

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import flask
import unittest
import warnings
from flask.testsuite import FlaskTestCase, emits_module_deprecation_warning
from werkzeug.exceptions import NotFound
from werkzeug.http import parse_cache_control_header
from jinja2 import TemplateNotFound


# import moduleapp here because it uses deprecated features and we don't
# want to see the warnings
warnings.simplefilter('ignore', DeprecationWarning)
from moduleapp import app as moduleapp
warnings.simplefilter('default', DeprecationWarning)


class ModuleTestCase(FlaskTestCase):

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
        self.assert_equal(c.get('/').data, 'the index')
        self.assert_equal(c.get('/admin/').data, 'admin index')
        self.assert_equal(c.get('/admin/login').data, 'admin login')
        self.assert_equal(c.get('/admin/logout').data, 'admin logout')

    @emits_module_deprecation_warning
    def test_default_endpoint_name(self):
        app = flask.Flask(__name__)
        mod = flask.Module(__name__, 'frontend')
        def index():
            return 'Awesome'
        mod.add_url_rule('/', view_func=index)
        app.register_module(mod)
        rv = app.test_client().get('/')
        self.assert_equal(rv.data, 'Awesome')
        with app.test_request_context():
            self.assert_equal(flask.url_for('frontend.index'), '/')

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

        self.assert_equal(c.get('/').data, 'the index')
        self.assert_equal(catched, ['before-app', 'after-app'])
        del catched[:]

        self.assert_equal(c.get('/admin/').data, 'the admin')
        self.assert_equal(catched, ['before-app', 'before-admin',
                           'after-admin', 'after-app'])

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
        self.assert_equal(c.get('/').data, '13')
        self.assert_equal(c.get('/admin/').data, '123')

    @emits_module_deprecation_warning
    def test_late_binding(self):
        app = flask.Flask(__name__)
        admin = flask.Module(__name__, 'admin')
        @admin.route('/')
        def index():
            return '42'
        app.register_module(admin, url_prefix='/admin')
        self.assert_equal(app.test_client().get('/admin/').data, '42')

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
        self.assert_equal(rv.status_code, 404)
        self.assert_equal(rv.data, 'not found')
        rv = c.get('/error')
        self.assert_equal(rv.status_code, 500)
        self.assert_equal('internal server error', rv.data)

    def test_templates_and_static(self):
        app = moduleapp
        app.testing = True
        c = app.test_client()

        rv = c.get('/')
        self.assert_equal(rv.data, 'Hello from the Frontend')
        rv = c.get('/admin/')
        self.assert_equal(rv.data, 'Hello from the Admin')
        rv = c.get('/admin/index2')
        self.assert_equal(rv.data, 'Hello from the Admin')
        rv = c.get('/admin/static/test.txt')
        self.assert_equal(rv.data.strip(), 'Admin File')
        rv = c.get('/admin/static/css/test.css')
        self.assert_equal(rv.data.strip(), '/* nested file */')

        with app.test_request_context():
            self.assert_equal(flask.url_for('admin.static', filename='test.txt'),
                              '/admin/static/test.txt')

        with app.test_request_context():
            try:
                flask.render_template('missing.html')
            except TemplateNotFound, e:
                self.assert_equal(e.name, 'missing.html')
            else:
                self.assert_(0, 'expected exception')

        with flask.Flask(__name__).test_request_context():
            self.assert_equal(flask.render_template('nested/nested.txt'), 'I\'m nested')

    def test_safe_access(self):
        app = moduleapp

        with app.test_request_context():
            f = app.view_functions['admin.static']

            try:
                f('/etc/passwd')
            except NotFound:
                pass
            else:
                self.assert_(0, 'expected exception')
            try:
                f('../__init__.py')
            except NotFound:
                pass
            else:
                self.assert_(0, 'expected exception')

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
                    self.assert_(0, 'expected exception')
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
        self.assert_equal(c.get('/foo/').data, 'index')
        self.assert_equal(c.get('/foo/bar').data, 'bar')


class BlueprintTestCase(FlaskTestCase):

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

        self.assert_equal(c.get('/frontend-no').data, 'frontend says no')
        self.assert_equal(c.get('/backend-no').data, 'backend says no')
        self.assert_equal(c.get('/what-is-a-sideend').data, 'application itself says no')

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
        self.assert_equal(c.get('/1/foo').data, u'23/42')
        self.assert_equal(c.get('/2/foo').data, u'19/42')
        self.assert_equal(c.get('/1/bar').data, u'23')
        self.assert_equal(c.get('/2/bar').data, u'19')

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

        self.assert_equal(c.get('/de/').data, '/de/about')
        self.assert_equal(c.get('/de/about').data, '/de/')

    def test_templates_and_static(self):
        from blueprintapp import app
        c = app.test_client()

        rv = c.get('/')
        self.assert_equal(rv.data, 'Hello from the Frontend')
        rv = c.get('/admin/')
        self.assert_equal(rv.data, 'Hello from the Admin')
        rv = c.get('/admin/index2')
        self.assert_equal(rv.data, 'Hello from the Admin')
        rv = c.get('/admin/static/test.txt')
        self.assert_equal(rv.data.strip(), 'Admin File')
        rv = c.get('/admin/static/css/test.css')
        self.assert_equal(rv.data.strip(), '/* nested file */')

        # try/finally, in case other tests use this app for Blueprint tests.
        max_age_default = app.config['SEND_FILE_MAX_AGE_DEFAULT']
        try:
            expected_max_age = 3600
            if app.config['SEND_FILE_MAX_AGE_DEFAULT'] == expected_max_age:
                expected_max_age = 7200
            app.config['SEND_FILE_MAX_AGE_DEFAULT'] = expected_max_age
            rv = c.get('/admin/static/css/test.css')
            cc = parse_cache_control_header(rv.headers['Cache-Control'])
            self.assert_equal(cc.max_age, expected_max_age)
        finally:
            app.config['SEND_FILE_MAX_AGE_DEFAULT'] = max_age_default

        with app.test_request_context():
            self.assert_equal(flask.url_for('admin.static', filename='test.txt'),
                              '/admin/static/test.txt')

        with app.test_request_context():
            try:
                flask.render_template('missing.html')
            except TemplateNotFound, e:
                self.assert_equal(e.name, 'missing.html')
            else:
                self.assert_(0, 'expected exception')

        with flask.Flask(__name__).test_request_context():
            self.assert_equal(flask.render_template('nested/nested.txt'), 'I\'m nested')

    def test_default_static_cache_timeout(self):
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
                self.assert_equal(cc.max_age, 100)
        finally:
            app.config['SEND_FILE_MAX_AGE_DEFAULT'] = max_age_default

    def test_templates_list(self):
        from blueprintapp import app
        templates = sorted(app.jinja_env.list_templates())
        self.assert_equal(templates, ['admin/index.html',
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
        self.assert_equal(c.get('/fe').data.strip(), '/be')
        self.assert_equal(c.get('/fe2').data.strip(), '/fe')
        self.assert_equal(c.get('/be').data.strip(), '/fe')

    def test_empty_url_defaults(self):
        bp = flask.Blueprint('bp', __name__)

        @bp.route('/', defaults={'page': 1})
        @bp.route('/page/<int:page>')
        def something(page):
            return str(page)

        app = flask.Flask(__name__)
        app.register_blueprint(bp)

        c = app.test_client()
        self.assert_equal(c.get('/').data, '1')
        self.assert_equal(c.get('/page/2').data, '2')

    def test_route_decorator_custom_endpoint(self):

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
        self.assertEqual(c.get('/').data, 'index')
        self.assertEqual(c.get('/py/foo').data, 'bp.foo')
        self.assertEqual(c.get('/py/bar').data, 'bp.bar')
        self.assertEqual(c.get('/py/bar/123').data, 'bp.123')
        self.assertEqual(c.get('/py/bar/foo').data, 'bp.bar_foo')

    def test_route_decorator_custom_endpoint_with_dots(self):
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

        self.assertRaises(
            AssertionError,
            lambda: bp.add_url_rule(
                '/bar/123', endpoint='bar.123', view_func=foo_foo_foo
            )
        )

        self.assertRaises(
            AssertionError,
            bp.route('/bar/123', endpoint='bar.123'),
            lambda: None
        )

        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')

        c = app.test_client()
        self.assertEqual(c.get('/py/foo').data, 'bp.foo')
        # The rule's din't actually made it through
        rv = c.get('/py/bar')
        assert rv.status_code == 404
        rv = c.get('/py/bar/123')
        assert rv.status_code == 404

    def test_template_filter(self):
        bp = flask.Blueprint('bp', __name__)
        @bp.app_template_filter()
        def my_reverse(s):
            return s[::-1]
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('my_reverse' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['my_reverse'], my_reverse)
        self.assert_equal(app.jinja_env.filters['my_reverse']('abcd'), 'dcba')

    def test_add_template_filter(self):
        bp = flask.Blueprint('bp', __name__)
        def my_reverse(s):
            return s[::-1]
        bp.add_app_template_filter(my_reverse)
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('my_reverse' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['my_reverse'], my_reverse)
        self.assert_equal(app.jinja_env.filters['my_reverse']('abcd'), 'dcba')

    def test_template_filter_with_name(self):
        bp = flask.Blueprint('bp', __name__)
        @bp.app_template_filter('strrev')
        def my_reverse(s):
            return s[::-1]
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('strrev' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['strrev'], my_reverse)
        self.assert_equal(app.jinja_env.filters['strrev']('abcd'), 'dcba')

    def test_add_template_filter_with_name(self):
        bp = flask.Blueprint('bp', __name__)
        def my_reverse(s):
            return s[::-1]
        bp.add_app_template_filter(my_reverse, 'strrev')
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('strrev' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['strrev'], my_reverse)
        self.assert_equal(app.jinja_env.filters['strrev']('abcd'), 'dcba')

    def test_template_filter_with_template(self):
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
        self.assert_equal(rv.data, 'dcba')

    def test_template_filter_after_route_with_template(self):
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
        self.assert_equal(rv.data, 'dcba')

    def test_add_template_filter_with_template(self):
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
        self.assert_equal(rv.data, 'dcba')

    def test_template_filter_with_name_and_template(self):
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
        self.assert_equal(rv.data, 'dcba')

    def test_add_template_filter_with_name_and_template(self):
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
        self.assert_equal(rv.data, 'dcba')

    def test_template_test(self):
        bp = flask.Blueprint('bp', __name__)
        @bp.app_template_test()
        def is_boolean(value):
            return isinstance(value, bool)
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('is_boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['is_boolean'], is_boolean)
        self.assert_(app.jinja_env.tests['is_boolean'](False))

    def test_add_template_test(self):
        bp = flask.Blueprint('bp', __name__)
        def is_boolean(value):
            return isinstance(value, bool)
        bp.add_app_template_test(is_boolean)
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('is_boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['is_boolean'], is_boolean)
        self.assert_(app.jinja_env.tests['is_boolean'](False))

    def test_template_test_with_name(self):
        bp = flask.Blueprint('bp', __name__)
        @bp.app_template_test('boolean')
        def is_boolean(value):
            return isinstance(value, bool)
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['boolean'], is_boolean)
        self.assert_(app.jinja_env.tests['boolean'](False))

    def test_add_template_test_with_name(self):
        bp = flask.Blueprint('bp', __name__)
        def is_boolean(value):
            return isinstance(value, bool)
        bp.add_app_template_test(is_boolean, 'boolean')
        app = flask.Flask(__name__)
        app.register_blueprint(bp, url_prefix='/py')
        self.assert_('boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['boolean'], is_boolean)
        self.assert_(app.jinja_env.tests['boolean'](False))

    def test_template_test_with_template(self):
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
        self.assert_('Success!' in rv.data)

    def test_template_test_after_route_with_template(self):
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
        self.assert_('Success!' in rv.data)

    def test_add_template_test_with_template(self):
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
        self.assert_('Success!' in rv.data)

    def test_template_test_with_name_and_template(self):
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
        self.assert_('Success!' in rv.data)

    def test_add_template_test_with_name_and_template(self):
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
        self.assert_('Success!' in rv.data)

def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(BlueprintTestCase))
    suite.addTest(unittest.makeSuite(ModuleTestCase))
    return suite
