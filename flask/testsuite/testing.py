# -*- coding: utf-8 -*-
"""
    flask.testsuite.testing
    ~~~~~~~~~~~~~~~~~~~~~~~

    Test client and more.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

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

    def test_redirect_keep_session(self):
        app = flask.Flask(__name__)
        app.secret_key = 'testing'

        @app.route('/', methods=['GET', 'POST'])
        def index():
            if flask.request.method == 'POST':
                return flask.redirect('/getsession')
            flask.session['data'] = 'foo'
            return 'index'

        @app.route('/getsession')
        def get_session():
            return flask.session.get('data', '<missing>')

        with app.test_client() as c:
            rv = c.get('/getsession')
            assert rv.data == '<missing>'

            rv = c.get('/')
            assert rv.data == 'index'
            assert flask.session.get('data') == 'foo'
            rv = c.post('/', data={}, follow_redirects=True)
            assert rv.data == 'foo'

            # This support requires a new Werkzeug version
            if not hasattr(c, 'redirect_client'):
                assert flask.session.get('data') == 'foo'

            rv = c.get('/getsession')
            assert rv.data == 'foo'

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
            with c.session_transaction() as sess:
                self.assert_equal(len(sess), 1)
                self.assert_equal(sess['foo'], [42])

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
            self.assert_(req is not None)
            with c.session_transaction():
                self.assert_(req is flask.request._get_current_object())

    def test_session_transaction_needs_cookies(self):
        app = flask.Flask(__name__)
        app.testing = True
        c = app.test_client(use_cookies=False)
        try:
            with c.session_transaction() as s:
                pass
        except RuntimeError, e:
            self.assert_('cookies' in str(e))
        else:
            self.fail('Expected runtime error')

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
            self.assert_equal(flask.g.value, 42)
            self.assert_equal(resp.data, 'Hello World!')
            self.assert_equal(resp.status_code, 200)

            resp = c.get('/other')
            self.assert_(not hasattr(flask.g, 'value'))
            self.assert_('Internal Server Error' in resp.data)
            self.assert_equal(resp.status_code, 500)
            flask.g.value = 23

        try:
            flask.g.value
        except (AttributeError, RuntimeError):
            pass
        else:
            raise AssertionError('some kind of exception expected')

    def test_reuse_client(self):
        app = flask.Flask(__name__)
        c = app.test_client()

        with c:
            self.assert_equal(c.get('/').status_code, 404)

        with c:
            self.assert_equal(c.get('/').status_code, 404)

    def test_test_client_calls_teardown_handlers(self):
        app = flask.Flask(__name__)
        called = []
        @app.teardown_request
        def remember(error):
            called.append(error)

        with app.test_client() as c:
            self.assert_equal(called, [])
            c.get('/')
            self.assert_equal(called, [])
        self.assert_equal(called, [None])

        del called[:]
        with app.test_client() as c:
            self.assert_equal(called, [])
            c.get('/')
            self.assert_equal(called, [])
            c.get('/')
            self.assert_equal(called, [None])
        self.assert_equal(called, [None, None])


class SubdomainTestCase(FlaskTestCase):

    def setUp(self):
        self.app = flask.Flask(__name__)
        self.app.config['SERVER_NAME'] = 'example.com'
        self.client = self.app.test_client()

        self._ctx = self.app.test_request_context()
        self._ctx.push()

    def tearDown(self):
        if self._ctx is not None:
            self._ctx.pop()

    def test_subdomain(self):
        @self.app.route('/', subdomain='<company_id>')
        def view(company_id):
            return company_id

        url = flask.url_for('view', company_id='xxx')
        response = self.client.get(url)

        self.assertEquals(200, response.status_code)
        self.assertEquals('xxx', response.data)


    def test_nosubdomain(self):
        @self.app.route('/<company_id>')
        def view(company_id):
            return company_id

        url = flask.url_for('view', company_id='xxx')
        response = self.client.get(url)

        self.assertEquals(200, response.status_code)
        self.assertEquals('xxx', response.data)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestToolsTestCase))
    suite.addTest(unittest.makeSuite(SubdomainTestCase))
    return suite
