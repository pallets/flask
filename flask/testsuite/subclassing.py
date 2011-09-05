# -*- coding: utf-8 -*-
"""
    flask.testsuite.subclassing
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Test that certain behavior of flask can be customized by
    subclasses.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import flask
import unittest
from StringIO import StringIO
from logging import StreamHandler
from flask.testsuite import FlaskTestCase


class FlaskSubclassingTestCase(FlaskTestCase):

    def test_supressed_exception_logging(self):
        class SupressedFlask(flask.Flask):
            def log_exception(self, exc_info):
                pass

        out = StringIO()
        app = SupressedFlask(__name__)
        app.logger_name = 'flask_tests/test_supressed_exception_logging'
        app.logger.addHandler(StreamHandler(out))

        @app.route('/')
        def index():
            1/0

        rv = app.test_client().get('/')
        self.assert_equal(rv.status_code, 500)
        self.assert_('Internal Server Error' in rv.data)

        err = out.getvalue()
        self.assert_equal(err, '')


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(FlaskSubclassingTestCase))
    return suite
