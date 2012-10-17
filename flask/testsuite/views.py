# -*- coding: utf-8 -*-
"""
    flask.testsuite.views
    ~~~~~~~~~~~~~~~~~~~~~

    Pluggable views.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import flask
import flask.views
import unittest
from flask.testsuite import FlaskTestCase
from werkzeug.http import parse_set_header

class ViewTestCase(FlaskTestCase):

    def common_test(self, app):
        c = app.test_client()

        self.assert_equal(c.get('/').data, 'GET')
        self.assert_equal(c.post('/').data, 'POST')
        self.assert_equal(c.put('/').status_code, 405)
        meths = parse_set_header(c.open('/', method='OPTIONS').headers['Allow'])
        self.assert_equal(sorted(meths), ['GET', 'HEAD', 'OPTIONS', 'POST'])

    def test_basic_view(self):
        app = flask.Flask(__name__)

        class Index(flask.views.View):
            methods = ['GET', 'POST']
            def dispatch_request(self):
                return flask.request.method

        app.add_url_rule('/', view_func=Index.as_view('index'))
        self.common_test(app)

    def test_method_based_view(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                return 'GET'
            def post(self):
                return 'POST'

        app.add_url_rule('/', view_func=Index.as_view('index'))

        self.common_test(app)

    def test_view_patching(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                1/0
            def post(self):
                1/0

        class Other(Index):
            def get(self):
                return 'GET'
            def post(self):
                return 'POST'

        view = Index.as_view('index')
        view.view_class = Other
        app.add_url_rule('/', view_func=view)
        self.common_test(app)

    def test_view_inheritance(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                return 'GET'
            def post(self):
                return 'POST'

        class BetterIndex(Index):
            def delete(self):
                return 'DELETE'

        app.add_url_rule('/', view_func=BetterIndex.as_view('index'))
        c = app.test_client()

        meths = parse_set_header(c.open('/', method='OPTIONS').headers['Allow'])
        self.assert_equal(sorted(meths), ['DELETE', 'GET', 'HEAD', 'OPTIONS', 'POST'])

    def test_view_decorators(self):
        app = flask.Flask(__name__)

        def add_x_parachute(f):
            def new_function(*args, **kwargs):
                resp = flask.make_response(f(*args, **kwargs))
                resp.headers['X-Parachute'] = 'awesome'
                return resp
            return new_function

        class Index(flask.views.View):
            decorators = [add_x_parachute]
            def dispatch_request(self):
                return 'Awesome'

        app.add_url_rule('/', view_func=Index.as_view('index'))
        c = app.test_client()
        rv = c.get('/')
        self.assert_equal(rv.headers['X-Parachute'], 'awesome')
        self.assert_equal(rv.data, 'Awesome')

    def test_implicit_head(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                return flask.Response('Blub', headers={
                    'X-Method': flask.request.method
                })

        app.add_url_rule('/', view_func=Index.as_view('index'))
        c = app.test_client()
        rv = c.get('/')
        self.assert_equal(rv.data, 'Blub')
        self.assert_equal(rv.headers['X-Method'], 'GET')
        rv = c.head('/')
        self.assert_equal(rv.data, '')
        self.assert_equal(rv.headers['X-Method'], 'HEAD')

    def test_explicit_head(self):
        app = flask.Flask(__name__)

        class Index(flask.views.MethodView):
            def get(self):
                return 'GET'
            def head(self):
                return flask.Response('', headers={'X-Method': 'HEAD'})

        app.add_url_rule('/', view_func=Index.as_view('index'))
        c = app.test_client()
        rv = c.get('/')
        self.assert_equal(rv.data, 'GET')
        rv = c.head('/')
        self.assert_equal(rv.data, '')
        self.assert_equal(rv.headers['X-Method'], 'HEAD')

    def test_endpoint_override(self):
        app = flask.Flask(__name__)
        app.debug = True

        class Index(flask.views.View):
            methods = ['GET', 'POST']
            def dispatch_request(self):
                return flask.request.method

        app.add_url_rule('/', view_func=Index.as_view('index'))

        with self.assert_raises(AssertionError):
            app.add_url_rule('/', view_func=Index.as_view('index'))

        # But these tests should still pass. We just log a warning.
        self.common_test(app)


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(ViewTestCase))
    return suite
