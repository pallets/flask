# -*- coding: utf-8 -*-
"""
    tests.examples
    ~~~~~~~~~~~~~~~~~~~~~~~~

    Tests the examples.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import unittest
from tests import add_to_path


def setup_path():
    example_path = os.path.join(os.path.dirname(__file__),
                                os.pardir, os.pardir, 'examples')
    add_to_path(os.path.join(example_path, 'flaskr'))
    add_to_path(os.path.join(example_path, 'minitwit'))


def suite():
    setup_path()
    suite = unittest.TestSuite()
    try:
        from minitwit_tests import TestMiniTwit
    except ImportError:
        pass
    else:
        suite.addTest(unittest.makeSuite(TestMiniTwit))
    try:
        from flaskr_tests import TestFlaskr
    except ImportError:
        pass
    else:
        suite.addTest(unittest.makeSuite(TestFlaskr))
    return suite
