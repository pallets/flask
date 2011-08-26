# -*- coding: utf-8 -*-
"""
    flask.testsuite.testing
    ~~~~~~~~~~~~~~~~~~~~~~~

    Test client and more.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import flask
import unittest
from flask.testsuite import FlaskTestCase


class TestToolsTestCase(FlaskTestCase):

    def test_environ_defaults_from_config(self):
        app = flask.Flask(__name__)
        app.testing = True
        app.config['SERVER_NAME'] = 'example.com:1234'
        app.config['APPLICATION_ROOT'] = '/foo'
        @app.route('/')
        def index():
            return flask.request.url

        ctx = app.test_request_context()
        self.assert_equal(ctx.request.url, 'http://example.com:1234/foo/')
        with app.test_client() as c:
            rv = c.get('/')
            self.assert_equal(rv.data, 'http://example.com:1234/foo/')

    def test_environ_defaults(self):
        app = flask.Flask(__name__)
        app.testing = True
        @app.route('/')
        def index():
            return flask.request.url

        ctx = app.test_request_context()
        self.assert_equal(ctx.request.url, 'http://localhost/')
        with app.test_client() as c:
            rv = c.get('/')
            self.assert_equal(rv.data, 'http://localhost/')

    def test_session_transactions(self):
        app = flask.Flask(__name__)
        app.testing = True
        app.secret_key = 'testing'

        @app.route('/')
        def index():
            return unicode(flask.session['foo'])

        with app.test_client() as c:
            with c.session_transaction() as sess:
                self.assert_equal(len(sess), 0)
                sess['foo'] = [42]
                self.assert_equal(len(sess), 1)
            rv = c.get('/')
            self.assert_equal(rv.data, '[42]')

    def test_session_transactions_no_null_sessions(self):
        app = flask.Flask(__name__)
        app.testing = True

        with app.test_client() as c:
            try:
                with c.session_transaction() as sess:
                    pass
            except RuntimeError, e:
                self.assert_('Session backend did not open a session' in str(e))
            else:
                self.fail('Expected runtime error')

    def test_session_transactions_keep_context(self):
        app = flask.Flask(__name__)
        app.testing = True
        app.secret_key = 'testing'

        with app.test_client() as c:
            rv = c.get('/')
            req = flask.request._get_current_object()
            with c.session_transaction():
                self.assert_(req is flask.request._get_current_object())

    def test_test_client_context_binding(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            flask.g.value = 42
            return 'Hello World!'

        @app.route('/other')
        def other():
            1/0

        with app.test_client() as c:
            resp = c.get('/')
            assert flask.g.value == 42
            assert resp.data == 'Hello World!'
            assert resp.status_code == 200

            resp = c.get('/other')
            assert not hasattr(flask.g, 'value')
            assert 'Internal Server Error' in resp.data
            assert resp.status_code == 500
            flask.g.value = 23

        try:
            flask.g.value
        except (AttributeError, RuntimeError):
            pass
        else:
            raise AssertionError('some kind of exception expected')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestToolsTestCase))
    return suite
