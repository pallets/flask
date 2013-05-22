# -*- coding: utf-8 -*-
"""
    flask.testsuite.reqctx
    ~~~~~~~~~~~~~~~~~~~~~~

    Tests the request context.

    :copyright: (c) 2012 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import flask
import unittest
try:
    from greenlet import greenlet
except ImportError:
    greenlet = None
from flask.testsuite import FlaskTestCase


class RequestContextTestCase(FlaskTestCase):

    def test_teardown_on_pop(self):
        buffer = []
        app = flask.Flask(__name__)
        @app.teardown_request
        def end_of_request(exception):
            buffer.append(exception)

        ctx = app.test_request_context()
        ctx.push()
        self.assert_equal(buffer, [])
        ctx.pop()
        self.assert_equal(buffer, [None])

    def test_proper_test_request_context(self):
        app = flask.Flask(__name__)
        app.config.update(
            SERVER_NAME='localhost.localdomain:5000'
        )

        @app.route('/')
        def index():
            return None

        @app.route('/', subdomain='foo')
        def sub():
            return None

        with app.test_request_context('/'):
            self.assert_equal(flask.url_for('index', _external=True), 'http://localhost.localdomain:5000/')

        with app.test_request_context('/'):
            self.assert_equal(flask.url_for('sub', _external=True), 'http://foo.localhost.localdomain:5000/')

        try:
            with app.test_request_context('/', environ_overrides={'HTTP_HOST': 'localhost'}):
                pass
        except Exception as e:
            self.assert_true(isinstance(e, ValueError))
            self.assert_equal(str(e), "the server name provided " +
                    "('localhost.localdomain:5000') does not match the " + \
                    "server name from the WSGI environment ('localhost')")

        try:
            app.config.update(SERVER_NAME='localhost')
            with app.test_request_context('/', environ_overrides={'SERVER_NAME': 'localhost'}):
                pass
        except ValueError as e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

        try:
            app.config.update(SERVER_NAME='localhost:80')
            with app.test_request_context('/', environ_overrides={'SERVER_NAME': 'localhost:80'}):
                pass
        except ValueError as e:
            raise ValueError(
                "No ValueError exception should have been raised \"%s\"" % e
            )

    def test_context_binding(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return 'Hello %s!' % flask.request.args['name']
        @app.route('/meh')
        def meh():
            return flask.request.url

        with app.test_request_context('/?name=World'):
            self.assert_equal(index(), 'Hello World!')
        with app.test_request_context('/meh'):
            self.assert_equal(meh(), 'http://localhost/meh')
        self.assert_true(flask._request_ctx_stack.top is None)

    def test_context_test(self):
        app = flask.Flask(__name__)
        self.assert_false(flask.request)
        self.assert_false(flask.has_request_context())
        ctx = app.test_request_context()
        ctx.push()
        try:
            self.assert_true(flask.request)
            self.assert_true(flask.has_request_context())
        finally:
            ctx.pop()

    def test_manual_context_binding(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return 'Hello %s!' % flask.request.args['name']

        ctx = app.test_request_context('/?name=World')
        ctx.push()
        self.assert_equal(index(), 'Hello World!')
        ctx.pop()
        try:
            index()
        except RuntimeError:
            pass
        else:
            self.assert_true(0, 'expected runtime error')

    def test_greenlet_context_copying(self):
        app = flask.Flask(__name__)
        greenlets = []

        @app.route('/')
        def index():
            reqctx = flask._request_ctx_stack.top.copy()
            def g():
                self.assert_false(flask.request)
                self.assert_false(flask.current_app)
                with reqctx:
                    self.assert_true(flask.request)
                    self.assert_equal(flask.current_app, app)
                    self.assert_equal(flask.request.path, '/')
                    self.assert_equal(flask.request.args['foo'], 'bar')
                self.assert_false(flask.request)
                return 42
            greenlets.append(greenlet(g))
            return 'Hello World!'

        rv = app.test_client().get('/?foo=bar')
        self.assert_equal(rv.data, b'Hello World!')

        result = greenlets[0].run()
        self.assert_equal(result, 42)

    def test_greenlet_context_copying_api(self):
        app = flask.Flask(__name__)
        greenlets = []

        @app.route('/')
        def index():
            reqctx = flask._request_ctx_stack.top.copy()
            @flask.copy_current_request_context
            def g():
                self.assert_true(flask.request)
                self.assert_equal(flask.current_app, app)
                self.assert_equal(flask.request.path, '/')
                self.assert_equal(flask.request.args['foo'], 'bar')
                return 42
            greenlets.append(greenlet(g))
            return 'Hello World!'

        rv = app.test_client().get('/?foo=bar')
        self.assert_equal(rv.data, b'Hello World!')

        result = greenlets[0].run()
        self.assert_equal(result, 42)

    # Disable test if we don't have greenlets available
    if greenlet is None:
        test_greenlet_context_copying = None
        test_greenlet_context_copying_api = None


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(RequestContextTestCase))
    return suite
