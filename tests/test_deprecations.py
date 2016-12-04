# -*- coding: utf-8 -*-
"""
    tests.deprecations
    ~~~~~~~~~~~~~~~~~~

    Tests deprecation support. Not used currently.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import flask


class TestRequestDeprecation(object):

    def test_request_json(self, recwarn):
        """Request.json is deprecated"""
        app = flask.Flask(__name__)
        app.testing = True

        @app.route('/', methods=['POST'])
        def index():
            assert flask.request.json == {'spam': 42}
            print(flask.request.json)
            return 'OK'

        c = app.test_client()
        c.post('/', data='{"spam": 42}', content_type='application/json')
        recwarn.pop(DeprecationWarning)

    def test_request_module(self, recwarn):
        """Request.module is deprecated"""
        app = flask.Flask(__name__)
        app.testing = True

        @app.route('/')
        def index():
            assert flask.request.module is None
            return 'OK'

        c = app.test_client()
        c.get('/')
        recwarn.pop(DeprecationWarning)
