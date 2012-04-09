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

    def test_basic_support(self):
        app = flask.Flask(__name__)
        app.config['SERVER_NAME'] = 'localhost'
        app.config['PREFERRED_URL_SCHEME'] = 'https'

        @app.route('/')
        def index():
            pass

        with app.app_context():
            rv = flask.url_for('index')
            self.assert_equal(rv, 'https://localhost/')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(AppContextTestCase))
    return suite
