# -*- coding: utf-8 -*-
"""
    flask.testsuite
    ~~~~~~~~~~~~~~~

    Tests Flask itself.  The majority of Flask is already tested
    as part of Werkzeug.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import flask
import warnings
import unittest
from StringIO import StringIO
from functools import update_wrapper
from contextlib import contextmanager
from werkzeug.utils import import_string, find_modules


def add_to_path(path):
    def _samefile(x, y):
        try:
            return os.path.samefile(x, y)
        except (IOError, OSError):
            return False
    for entry in sys.path:
        try:
            if os.path.samefile(path, entry):
                return
        except (OSError, IOError):
            pass
    sys.path.append(path)


def setup_paths():
    add_to_path(os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'test_apps')))


def iter_suites():
    for module in find_modules(__name__):
        mod = import_string(module)
        if hasattr(mod, 'suite'):
            yield mod.suite()


@contextmanager
def catch_warnings():
    """Catch warnings in a with block in a list"""
    # make sure deprecation warnings are active in tests
    warnings.simplefilter('default', category=DeprecationWarning)

    filters = warnings.filters
    warnings.filters = filters[:]
    old_showwarning = warnings.showwarning
    log = []
    def showwarning(message, category, filename, lineno, file=None, line=None):
        log.append(locals())
    try:
        warnings.showwarning = showwarning
        yield log
    finally:
        warnings.filters = filters
        warnings.showwarning = old_showwarning


@contextmanager
def catch_stderr():
    """Catch stderr in a StringIO"""
    old_stderr = sys.stderr
    sys.stderr = rv = StringIO()
    try:
        yield rv
    finally:
        sys.stderr = old_stderr


def emits_module_deprecation_warning(f):
    def new_f(self, *args, **kwargs):
        with catch_warnings() as log:
            f(self, *args, **kwargs)
            self.assert_(log, 'expected deprecation warning')
            for entry in log:
                self.assert_('Modules are deprecated' in str(entry['message']))
    return update_wrapper(new_f, f)


class FlaskTestCase(unittest.TestCase):

    def ensure_clean_request_context(self):
        # make sure we're not leaking a request context since we are
        # testing flask internally in debug mode in a few cases
        self.assert_equal(flask._request_ctx_stack.top, None)

    def setup(self):
        pass

    def teardown(self):
        pass

    def setUp(self):
        self.setup()

    def tearDown(self):
        unittest.TestCase.tearDown(self)
        self.ensure_clean_request_context()
        self.teardown()

    def assert_equal(self, x, y):
        return self.assertEqual(x, y)


def suite():
    setup_paths()
    suite = unittest.TestSuite()
    for other_suite in iter_suites():
        suite.addTest(other_suite)
    return suite
