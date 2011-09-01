# -*- coding: utf-8 -*-
"""
    flask.testsuite.deprecations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests deprecation support.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import flask
import unittest
from flask.testsuite import FlaskTestCase, catch_warnings


class DeprecationsTestCase(FlaskTestCase):

    def test_init_jinja_globals(self):
        class MyFlask(flask.Flask):
            def init_jinja_globals(self):
                self.jinja_env.globals['foo'] = '42'

        with catch_warnings() as log:
            app = MyFlask(__name__)
            @app.route('/')
            def foo():
                return app.jinja_env.globals['foo']

            c = app.test_client()
            self.assert_equal(c.get('/').data, '42')
            self.assert_equal(len(log), 1)
            self.assert_('init_jinja_globals' in str(log[0]['message']))


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DeprecationsTestCase))
    return suite
