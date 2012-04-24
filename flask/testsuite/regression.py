# -*- coding: utf-8 -*-
"""
    flask.testsuite.regression
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests regressions.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import gc
import sys
import flask
import threading
import unittest
from werkzeug.test import run_wsgi_app, create_environ
from flask.testsuite import FlaskTestCase


_gc_lock = threading.Lock()


class _NoLeakAsserter(object):

    def __init__(self, testcase):
        self.testcase = testcase

    def __enter__(self):
        gc.disable()
        _gc_lock.acquire()
        loc = flask._request_ctx_stack._local

        # Force Python to track this dictionary at all times.
        # This is necessary since Python only starts tracking
        # dicts if they contain mutable objects.  It's a horrible,
        # horrible hack but makes this kinda testable.
        loc.__storage__['FOOO'] = [1, 2, 3]

        gc.collect()
        self.old_objects = len(gc.get_objects())

    def __exit__(self, exc_type, exc_value, tb):
        if not hasattr(sys, 'getrefcount'):
            gc.collect()
        new_objects = len(gc.get_objects())
        if new_objects > self.old_objects:
            self.testcase.fail('Example code leaked')
        _gc_lock.release()
        gc.enable()


class MemoryTestCase(FlaskTestCase):

    def assert_no_leak(self):
        return _NoLeakAsserter(self)

    def test_memory_consumption(self):
        app = flask.Flask(__name__)
        @app.route('/')
        def index():
            return flask.render_template('simple_template.html', whiskey=42)

        def fire():
            with app.test_client() as c:
                rv = c.get('/')
                self.assert_equal(rv.status_code, 200)
                self.assert_equal(rv.data, '<h1>42</h1>')

        # Trigger caches
        fire()

        # This test only works on CPython 2.7.
        if sys.version_info >= (2, 7) and \
                not hasattr(sys, 'pypy_translation_info'):
            with self.assert_no_leak():
                for x in xrange(10):
                    fire()


def suite():
    suite = unittest.TestSuite()
    suite.addTest(unittest.makeSuite(MemoryTestCase))
    return suite
