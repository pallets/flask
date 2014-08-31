# -*- coding: utf-8 -*-
"""
    tests.deprecations
    ~~~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests deprecation support.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import flask
import unittest
from tests import TestFlask, catch_warnings


class TestDeprecations(TestFlask):
    """not used currently"""


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(TestDeprecations))
    return suite
