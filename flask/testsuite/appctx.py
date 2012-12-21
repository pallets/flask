# -*- coding: utf-8 -*-
"""
    flask.testsuite.appctx
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests the application context.

    :copyright: (c) 2012 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import flask
import unittest
from flask.testsuite import FlaskTestCase


class AppContextTestCase(FlaskTestCase):

    def test_basic_url_generation(self):
        app = flask.Flask(__name__)
        app.config['SERVER_NAME'] = 'localhost'
        app.config['PREFERRED_URL_SCHEME'] = 'https'

        @app.route('/')
        def index():
            pass

        with app.app_context():
            rv = flask.url_for('index')
            self.assert_equal(rv, 'https://localhost/')

    def test_url_generation_requires_server_name(self):
        app = flask.Flask(__name__)
        with app.app_context():
            with self.assert_raises(RuntimeError):
                flask.url_for('index')

    def test_url_generation_without_context_fails(self):
        with self.assert_raises(RuntimeError):
            flask.url_for('index')

    def test_request_context_means_app_context(self):
        app = flask.Flask(__name__)
        with app.test_request_context():
            self.assert_equal(flask.current_app._get_current_object(), app)
        self.assert_equal(flask._app_ctx_stack.top, None)

    def test_app_context_provides_current_app(self):
        app = flask.Flask(__name__)
        with app.app_context():
            self.assert_equal(flask.current_app._get_current_object(), app)
        self.assert_equal(flask._app_ctx_stack.top, None)

    def test_app_tearing_down(self):
        cleanup_stuff = []
        app = flask.Flask(__name__)
        @app.teardown_appcontext
        def cleanup(exception):
            cleanup_stuff.append(exception)

        with app.app_context():
            pass

        self.assert_equal(cleanup_stuff, [None])

    def test_custom_app_ctx_globals_class(self):
        class CustomRequestGlobals(object):
            def __init__(self):
                self.spam = 'eggs'
        app = flask.Flask(__name__)
        app.app_ctx_globals_class = CustomRequestGlobals
        with app.app_context():
            self.assert_equal(
                flask.render_template_string('{{ g.spam }}'), 'eggs')

    def test_context_refcounts(self):
        called = []
        app = flask.Flask(__name__)
        @app.teardown_request
        def teardown_req(error=None):
            called.append('request')
        @app.teardown_appcontext
        def teardown_app(error=None):
            called.append('app')
        @app.route('/')
        def index():
            with flask._app_ctx_stack.top:
                with flask._request_ctx_stack.top:
                    pass
            self.assert_(flask._request_ctx_stack.request.environ
                ['werkzeug.request'] is not None)
        c = app.test_client()
        c.get('/')
        self.assertEqual(called, ['request', 'app'])


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AppContextTestCase))
    return suite
