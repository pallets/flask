# -*- coding: utf-8 -*-
"""
    flask.testsuite.templating
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Template functionality

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import flask
import unittest
from flask.testsuite import FlaskTestCase


class TemplatingTestCase(FlaskTestCase):

    def test_context_processing(self):
        app = flask.Flask(__name__)
        @app.context_processor
        def context_processor():
            return {'injected_value': 42}
        @app.route('/')
        def index():
            return flask.render_template('context_template.html', value=23)
        rv = app.test_client().get('/')
        self.assert_equal(rv.data, '<p>23|42')

    def test_original_win(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.render_template_string('{{ config }}', config=42)
        rv = app.test_client().get('/')
        self.assert_equal(rv.data, '42')

    def test_request_less_rendering(self):
        app = flask.Flask(__name__)
        app.config['WORLD_NAME'] = 'Special World'
        @app.context_processor
        def context_processor():
            return dict(foo=42)

        with app.app_context():
            rv = flask.render_template_string('Hello {{ config.WORLD_NAME }} '
                                              '{{ foo }}')
            self.assert_equal(rv, 'Hello Special World 42')

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
        self.assert_equal(rv.data.split(), ['42', '23', 'False', 'aha'])

    def test_escaping(self):
        text = '<p>Hello World!'
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.render_template('escaping_template.html', text=text,
                                         html=flask.Markup(text))
        lines = app.test_client().get('/').data.splitlines()
        self.assert_equal(lines, [
            '&lt;p&gt;Hello World!',
            '<p>Hello World!',
            '<p>Hello World!',
            '<p>Hello World!',
            '&lt;p&gt;Hello World!',
            '<p>Hello World!'
        ])

    def test_no_escaping(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            self.assert_equal(flask.render_template_string('{{ foo }}',
                              foo='<test>'), '<test>')
            self.assert_equal(flask.render_template('mail.txt', foo='<test>'),
                              '<test> Mail')

    def test_macros(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            macro = flask.get_template_attribute('_macro.html', 'hello')
            self.assert_equal(macro('World'), 'Hello World!')

    def test_template_filter(self):
        app = flask.Flask(__name__)
        @app.template_filter()
        def my_reverse(s):
            return s[::-1]
        self.assert_('my_reverse' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['my_reverse'], my_reverse)
        self.assert_equal(app.jinja_env.filters['my_reverse']('abcd'), 'dcba')

    def test_add_template_filter(self):
        app = flask.Flask(__name__)
        def my_reverse(s):
            return s[::-1]
        app.add_template_filter(my_reverse)
        self.assert_('my_reverse' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['my_reverse'], my_reverse)
        self.assert_equal(app.jinja_env.filters['my_reverse']('abcd'), 'dcba')

    def test_template_filter_with_name(self):
        app = flask.Flask(__name__)
        @app.template_filter('strrev')
        def my_reverse(s):
            return s[::-1]
        self.assert_('strrev' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['strrev'], my_reverse)
        self.assert_equal(app.jinja_env.filters['strrev']('abcd'), 'dcba')

    def test_add_template_filter_with_name(self):
        app = flask.Flask(__name__)
        def my_reverse(s):
            return s[::-1]
        app.add_template_filter(my_reverse, 'strrev')
        self.assert_('strrev' in app.jinja_env.filters.keys())
        self.assert_equal(app.jinja_env.filters['strrev'], my_reverse)
        self.assert_equal(app.jinja_env.filters['strrev']('abcd'), 'dcba')

    def test_template_filter_with_template(self):
        app = flask.Flask(__name__)
        @app.template_filter()
        def super_reverse(s):
            return s[::-1]
        @app.route('/')
        def index():
            return flask.render_template('template_filter.html', value='abcd')
        rv = app.test_client().get('/')
        self.assert_equal(rv.data, 'dcba')

    def test_add_template_filter_with_template(self):
        app = flask.Flask(__name__)
        def super_reverse(s):
            return s[::-1]
        app.add_template_filter(super_reverse)
        @app.route('/')
        def index():
            return flask.render_template('template_filter.html', value='abcd')
        rv = app.test_client().get('/')
        self.assert_equal(rv.data, 'dcba')

    def test_template_filter_with_name_and_template(self):
        app = flask.Flask(__name__)
        @app.template_filter('super_reverse')
        def my_reverse(s):
            return s[::-1]
        @app.route('/')
        def index():
            return flask.render_template('template_filter.html', value='abcd')
        rv = app.test_client().get('/')
        self.assert_equal(rv.data, 'dcba')

    def test_add_template_filter_with_name_and_template(self):
        app = flask.Flask(__name__)
        def my_reverse(s):
            return s[::-1]
        app.add_template_filter(my_reverse, 'super_reverse')
        @app.route('/')
        def index():
            return flask.render_template('template_filter.html', value='abcd')
        rv = app.test_client().get('/')
        self.assert_equal(rv.data, 'dcba')

    def test_template_test(self):
        app = flask.Flask(__name__)
        @app.template_test()
        def boolean(value):
            return isinstance(value, bool)
        self.assert_('boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['boolean'], boolean)
        self.assert_(app.jinja_env.tests['boolean'](False))

    def test_add_template_test(self):
        app = flask.Flask(__name__)
        def boolean(value):
            return isinstance(value, bool)
        app.add_template_test(boolean)
        self.assert_('boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['boolean'], boolean)
        self.assert_(app.jinja_env.tests['boolean'](False))

    def test_template_test_with_name(self):
        app = flask.Flask(__name__)
        @app.template_test('boolean')
        def is_boolean(value):
            return isinstance(value, bool)
        self.assert_('boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['boolean'], is_boolean)
        self.assert_(app.jinja_env.tests['boolean'](False))

    def test_add_template_test_with_name(self):
        app = flask.Flask(__name__)
        def is_boolean(value):
            return isinstance(value, bool)
        app.add_template_test(is_boolean, 'boolean')
        self.assert_('boolean' in app.jinja_env.tests.keys())
        self.assert_equal(app.jinja_env.tests['boolean'], is_boolean)
        self.assert_(app.jinja_env.tests['boolean'](False))

    def test_template_test_with_template(self):
        app = flask.Flask(__name__)
        @app.template_test()
        def boolean(value):
            return isinstance(value, bool)
        @app.route('/')
        def index():
            return flask.render_template('template_test.html', value=False)
        rv = app.test_client().get('/')
        self.assert_('Success!' in rv.data)

    def test_add_template_test_with_template(self):
        app = flask.Flask(__name__)
        def boolean(value):
            return isinstance(value, bool)
        app.add_template_test(boolean)
        @app.route('/')
        def index():
            return flask.render_template('template_test.html', value=False)
        rv = app.test_client().get('/')
        self.assert_('Success!' in rv.data)

    def test_template_test_with_name_and_template(self):
        app = flask.Flask(__name__)
        @app.template_test('boolean')
        def is_boolean(value):
            return isinstance(value, bool)
        @app.route('/')
        def index():
            return flask.render_template('template_test.html', value=False)
        rv = app.test_client().get('/')
        self.assert_('Success!' in rv.data)

    def test_add_template_test_with_name_and_template(self):
        app = flask.Flask(__name__)
        def is_boolean(value):
            return isinstance(value, bool)
        app.add_template_test(is_boolean, 'boolean')
        @app.route('/')
        def index():
            return flask.render_template('template_test.html', value=False)
        rv = app.test_client().get('/')
        self.assert_('Success!' in rv.data)

    def test_add_template_global(self):
        app = flask.Flask(__name__)
        @app.template_global()
        def get_stuff():
            return 42
        self.assert_('get_stuff' in app.jinja_env.globals.keys())
        self.assert_equal(app.jinja_env.globals['get_stuff'], get_stuff)
        self.assert_(app.jinja_env.globals['get_stuff'](), 42)
        with app.app_context():
            rv = flask.render_template_string('{{ get_stuff() }}')
            self.assert_equal(rv, '42')

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
        self.assert_equal(rv.data, 'Hello Custom World!')

    def test_iterable_loader(self):
        app = flask.Flask(__name__)
        @app.context_processor
        def context_processor():
            return {'whiskey': 'Jameson'}
        @app.route('/')
        def index():
            return flask.render_template(
                ['no_template.xml', # should skip this one
                'simple_template.html', # should render this
                'context_template.html'],
                value=23)

        rv = app.test_client().get('/')
        self.assert_equal(rv.data, '<h1>Jameson</h1>')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TemplatingTestCase))
    return suite
