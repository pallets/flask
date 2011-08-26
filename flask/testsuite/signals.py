# -*- coding: utf-8 -*-
"""
    flask.testsuite.signals
    ~~~~~~~~~~~~~~~~~~~~~~~

    Signalling.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import flask
import unittest
from flask.testsuite import FlaskTestCase


class SignalsTestCase(FlaskTestCase):

    def test_template_rendered(self):
        app = flask.Flask(__name__)

        @app.route('/')
        def index():
            return flask.render_template('simple_template.html', whiskey=42)

        recorded = []
        def record(sender, template, context):
            recorded.append((template, context))

        flask.template_rendered.connect(record, app)
        try:
            app.test_client().get('/')
            assert len(recorded) == 1
            template, context = recorded[0]
            assert template.name == 'simple_template.html'
            assert context['whiskey'] == 42
        finally:
            flask.template_rendered.disconnect(record, app)

    def test_request_signals(self):
        app = flask.Flask(__name__)
        calls = []

        def before_request_signal(sender):
            calls.append('before-signal')

        def after_request_signal(sender, response):
            assert response.data == 'stuff'
            calls.append('after-signal')

        @app.before_request
        def before_request_handler():
            calls.append('before-handler')

        @app.after_request
        def after_request_handler(response):
            calls.append('after-handler')
            response.data = 'stuff'
            return response

        @app.route('/')
        def index():
            calls.append('handler')
            return 'ignored anyway'

        flask.request_started.connect(before_request_signal, app)
        flask.request_finished.connect(after_request_signal, app)

        try:
            rv = app.test_client().get('/')
            assert rv.data == 'stuff'

            assert calls == ['before-signal', 'before-handler',
                             'handler', 'after-handler',
                             'after-signal']
        finally:
            flask.request_started.disconnect(before_request_signal, app)
            flask.request_finished.disconnect(after_request_signal, app)

    def test_request_exception_signal(self):
        app = flask.Flask(__name__)
        recorded = []

        @app.route('/')
        def index():
            1/0

        def record(sender, exception):
            recorded.append(exception)

        flask.got_request_exception.connect(record, app)
        try:
            assert app.test_client().get('/').status_code == 500
            assert len(recorded) == 1
            assert isinstance(recorded[0], ZeroDivisionError)
        finally:
            flask.got_request_exception.disconnect(record, app)


def suite():
    suite = unittest.TestSuite()
    if flask.signals_available:
        suite.addTest(unittest.makeSuite(SignalsTestCase))
    return suite
