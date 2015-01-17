# -*- coding: utf-8 -*-
"""
    flask.testsuite.examples
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the examples.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import unittest
from flask.testsuite import add_to_path


def setup_path():
    example_path = os.path.join(os.path.dirname(__file__),
                                os.pardir, os.pardir, 'examples')
    add_to_path(os.path.join(example_path, 'flaskr'))
    add_to_path(os.path.join(example_path, 'minitwit'))


def suite():
    setup_path()
    suite = unittest.TestSuite()
    try:
        from minitwit_tests import MiniTwitTestCase
    except ImportError:
        pass
    else:
        suite.addTest(unittest.makeSuite(MiniTwitTestCase))
    try:
        from flaskr_tests import FlaskrTestCase
    except ImportError:
        pass
    else:
        suite.addTest(unittest.makeSuite(FlaskrTestCase))
    return suite
