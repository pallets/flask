# -*- coding: utf-8 -*-
"""
    Flask Tests
    ~~~~~~~~~~~

    Tests Flask itself.  The majority of Flask is already tested
    as part of Werkzeug.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import flask
import unittest
import tempfile


class ContextTestCase(unittest.TestCase):

    def test_context_binding(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return 'Hello %s!' % flask.request.args['name']
        @app.route('/meh')
        def meh():
            return flask.request.url

        with app.test_request_context('/?name=World'):
            assert index() == 'Hello World!'
        with app.test_request_context('/meh'):
            assert meh() == 'http://localhost/meh'


class BasicFunctionality(unittest.TestCase):

    def test_request_dispatching(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.request.method
        @app.route('/more', methods=['GET', 'POST'])
        def more():
            return flask.request.method

        c = app.test_client()
        assert c.get('/').data == 'GET'
        rv = c.post('/')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD']
        rv = c.head('/')
        assert rv.status_code == 200
        assert not rv.data # head truncates
        assert c.post('/more').data == 'POST'
        assert c.get('/more').data == 'GET'
        rv = c.delete('/more')
        assert rv.status_code == 405
        assert sorted(rv.allow) == ['GET', 'HEAD', 'POST']

    def test_session(self):
        app = flask.Flask(__name__)
        app.secret_key = 'testkey'
        @app.route('/set', methods=['POST'])
        def set():
            flask.session['value'] = flask.request.form['value']
            return 'value set'
        @app.route('/get')
        def get():
            return flask.session['value']

        c = app.test_client()
        assert c.post('/set', data={'value': '42'}).data == 'value set'
        assert c.get('/get').data == '42'

    def test_request_processing(self):
        app = flask.Flask(__name__)
        evts = []
        @app.before_request
        def before_request():
            evts.append('before')
        @app.after_request
        def after_request(response):
            response.data += '|after'
            evts.append('after')
            return response
        @app.route('/')
        def index():
            assert 'before' in evts
            assert 'after' not in evts
            return 'request'
        assert 'after' not in evts
        rv = app.test_client().get('/').data
        assert 'after' in evts
        assert rv == 'request|after'

    def test_error_handling(self):
        app = flask.Flask(__name__)
        @app.errorhandler(404)
        def not_found(e):
            return 'not found', 404
        @app.errorhandler(500)
        def internal_server_error(e):
            return 'internal server error', 500
        @app.route('/')
        def index():
            flask.abort(404)
        @app.route('/error')
        def error():
            1/0
        c = app.test_client()
        rv = c.get('/')
        assert rv.status_code == 404
        assert rv.data == 'not found'
        rv = c.get('/error')
        assert rv.status_code == 500
        assert 'internal server error' in rv.data

    def test_response_creation(self):
        app = flask.Flask(__name__)
        @app.route('/unicode')
        def from_unicode():
            return u'Hällo Wörld'
        @app.route('/string')
        def from_string():
            return u'Hällo Wörld'.encode('utf-8')
        @app.route('/args')
        def from_tuple():
            return 'Meh', 400, {'X-Foo': 'Testing'}, 'text/plain'
        c = app.test_client()
        assert c.get('/unicode').data == u'Hällo Wörld'.encode('utf-8')
        assert c.get('/string').data == u'Hällo Wörld'.encode('utf-8')
        rv = c.get('/args')
        assert rv.data == 'Meh'
        assert rv.headers['X-Foo'] == 'Testing'
        assert rv.status_code == 400
        assert rv.mimetype == 'text/plain'

    def test_url_generation(self):
        app = flask.Flask(__name__)
        @app.route('/hello/<name>', methods=['POST'])
        def hello():
            pass
        with app.test_request_context():
            assert flask.url_for('hello', name='test x') == '/hello/test%20x'

    def test_static_files(self):
        app = flask.Flask(__name__)
        rv = app.test_client().get('/static/index.html')
        assert rv.status_code == 200
        assert rv.data.strip() == '<h1>Hello World!</h1>'
        with app.test_request_context():
            assert flask.url_for('static', filename='index.html') \
                == '/static/index.html'


class Templating(unittest.TestCase):

    def test_context_processing(self):
        app = flask.Flask(__name__)
        @app.context_processor
        def context_processor():
            return {'injected_value': 42}
        @app.route('/')
        def index():
            return flask.render_template('context_template.html', value=23)
        rv = app.test_client().get('/')
        assert rv.data == '<p>23|42'

    def test_escaping(self):
        text = '<p>Hello World!'
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.render_template('escaping_template.html', text=text,
                                         html=flask.Markup(text))
        lines = app.test_client().get('/').data.splitlines()
        assert lines == [
            '&lt;p&gt;Hello World!',
            '<p>Hello World!',
            '<p>Hello World!',
            '<p>Hello World!',
            '&lt;p&gt;Hello World!',
            '<p>Hello World!'
        ]


if __name__ == '__main__':
    unittest.main()
