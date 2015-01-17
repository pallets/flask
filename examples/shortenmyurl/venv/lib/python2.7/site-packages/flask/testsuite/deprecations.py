# -*- coding: utf-8 -*-
"""
    flask.testsuite.deprecations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests deprecation support.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import flask
import unittest
from flask.testsuite import FlaskTestCase, catch_warnings


class DeprecationsTestCase(FlaskTestCase):
    """not used currently"""


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(DeprecationsTestCase))
    return suite
