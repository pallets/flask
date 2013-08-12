# -*- coding: utf-8 -*-
"""
    flask.testsuite.regression
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests regressions.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import gc
import sys
import flask
import threading
import unittest
from werkzeug.exceptions import NotFound
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
                self.assert_equal(rv.data, b'<h1>42</h1>')

        # Trigger caches
        fire()

        # This test only works on CPython 2.7.
        if sys.version_info >= (2, 7) and \
                not hasattr(sys, 'pypy_translation_info'):
            with self.assert_no_leak():
                for x in range(10):
                    fire()

    def test_safe_join_toplevel_pardir(self):
        from flask.helpers import safe_join
        with self.assert_raises(NotFound):
            safe_join('/foo', '..')


class ExceptionTestCase(FlaskTestCase):

    def test_aborting(self):
        class Foo(Exception):
            whatever = 42
        app = flask.Flask(__name__)
        app.testing = True
        @app.errorhandler(Foo)
        def handle_foo(e):
            return str(e.whatever)
        @app.route('/')
        def index():
            raise flask.abort(flask.redirect(flask.url_for('test')))
        @app.route('/test')
        def test():
            raise Foo()

        with app.test_client() as c:
            rv = c.get('/')
            self.assertEqual(rv.headers['Location'], 'http://localhost/test')
            rv = c.get('/test')
            self.assertEqual(rv.data, b'42')


def suite():
    suite = unittest.TestSuite()
    if os.environ.get('RUN_FLASK_MEMORY_TESTS') == '1':
        suite.addTest(unittest.makeSuite(MemoryTestCase))
    suite.addTest(unittest.makeSuite(ExceptionTestCase))
    return suite
