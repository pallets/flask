# -*- coding: utf-8 -*-
"""
    tests.regression
    ~~~~~~~~~~~~~~~~~~~~~~~~~~

    Tests regressions.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import pytest

import os
import gc
import sys
import flask
import threading
from werkzeug.exceptions import NotFound


_gc_lock = threading.Lock()


class assert_no_leak(object):

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
        gc.collect()
        new_objects = len(gc.get_objects())
        if new_objects > self.old_objects:
            pytest.fail('Example code leaked')
        _gc_lock.release()
        gc.enable()


def test_memory_consumption():
    app = flask.Flask(__name__)

    @app.route('/')
    def index():
        return flask.render_template('simple_template.html', whiskey=42)

    def fire():
        with app.test_client() as c:
            rv = c.get('/')
            assert rv.status_code == 200
            assert rv.data == b'<h1>42</h1>'

    # Trigger caches
    fire()

    # This test only works on CPython 2.7.
    if sys.version_info >= (2, 7) and \
            not hasattr(sys, 'pypy_translation_info'):
        with assert_no_leak():
            for x in range(10):
                fire()


def test_safe_join_toplevel_pardir():
    from flask.helpers import safe_join
    with pytest.raises(NotFound):
        safe_join('/foo', '..')


def test_aborting():
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
        assert rv.headers['Location'] == 'http://localhost/test'
        rv = c.get('/test')
        assert rv.data == b'42'
