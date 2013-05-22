# -*- coding: utf-8 -*-
"""
    flask.testsuite
    ~~~~~~~~~~~~~~~

    Tests Flask itself.  The majority of Flask is already tested
    as part of Werkzeug.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import print_function

import os
import sys
import flask
import warnings
import unittest
from functools import update_wrapper
from contextlib import contextmanager
from werkzeug.utils import import_string, find_modules
from flask._compat import reraise, StringIO


def add_to_path(path):
    """Adds an entry to sys.path if it's not already there.  This does
    not append it but moves it to the front so that we can be sure it
    is loaded.
    """
    if not os.path.isdir(path):
        raise RuntimeError('Tried to add nonexisting path')

    def _samefile(x, y):
        if x == y:
            return True
        try:
            return os.path.samefile(x, y)
        except (IOError, OSError, AttributeError):
            # Windows has no samefile
            return False
    sys.path[:] = [x for x in sys.path if not _samefile(path, x)]
    sys.path.insert(0, path)


def iter_suites():
    """Yields all testsuites."""
    for module in find_modules(__name__):
        mod = import_string(module)
        if hasattr(mod, 'suite'):
            yield mod.suite()


def find_all_tests(suite):
    """Yields all the tests and their names from a given suite."""
    suites = [suite]
    while suites:
        s = suites.pop()
        try:
            suites.extend(s)
        except TypeError:
            yield s, '%s.%s.%s' % (
                s.__class__.__module__,
                s.__class__.__name__,
                s._testMethodName
            )


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
            self.assert_true(log, 'expected deprecation warning')
            for entry in log:
                self.assert_in('Modules are deprecated', str(entry['message']))
    return update_wrapper(new_f, f)


class FlaskTestCase(unittest.TestCase):
    """Baseclass for all the tests that Flask uses.  Use these methods
    for testing instead of the camelcased ones in the baseclass for
    consistency.
    """

    def ensure_clean_request_context(self):
        # make sure we're not leaking a request context since we are
        # testing flask internally in debug mode in a few cases
        leaks = []
        while flask._request_ctx_stack.top is not None:
            leaks.append(flask._request_ctx_stack.pop())
        self.assert_equal(leaks, [])

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

    def assert_raises(self, exc_type, callable=None, *args, **kwargs):
        catcher = _ExceptionCatcher(self, exc_type)
        if callable is None:
            return catcher
        with catcher:
            callable(*args, **kwargs)

    def assert_true(self, x, msg=None):
        self.assertTrue(x, msg)

    def assert_false(self, x, msg=None):
        self.assertFalse(x, msg)

    def assert_in(self, x, y):
        self.assertIn(x, y)

    def assert_not_in(self, x, y):
        self.assertNotIn(x, y)

    if sys.version_info[:2] == (2, 6):
        def assertIn(self, x, y):
            assert x in y, "%r unexpectedly not in %r" % (x, y)

        def assertNotIn(self, x, y):
            assert x not in y, "%r unexpectedly in %r" % (x, y)


class _ExceptionCatcher(object):

    def __init__(self, test_case, exc_type):
        self.test_case = test_case
        self.exc_type = exc_type

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_value, tb):
        exception_name = self.exc_type.__name__
        if exc_type is None:
            self.test_case.fail('Expected exception of type %r' %
                                exception_name)
        elif not issubclass(exc_type, self.exc_type):
            reraise(exc_type, exc_value, tb)
        return True


class BetterLoader(unittest.TestLoader):
    """A nicer loader that solves two problems.  First of all we are setting
    up tests from different sources and we're doing this programmatically
    which breaks the default loading logic so this is required anyways.
    Secondly this loader has a nicer interpolation for test names than the
    default one so you can just do ``run-tests.py ViewTestCase`` and it
    will work.
    """

    def getRootSuite(self):
        return suite()

    def loadTestsFromName(self, name, module=None):
        root = self.getRootSuite()
        if name == 'suite':
            return root

        all_tests = []
        for testcase, testname in find_all_tests(root):
            if testname == name or \
               testname.endswith('.' + name) or \
               ('.' + name + '.') in testname or \
               testname.startswith(name + '.'):
                all_tests.append(testcase)

        if not all_tests:
            raise LookupError('could not find test case for "%s"' % name)

        if len(all_tests) == 1:
            return all_tests[0]
        rv = unittest.TestSuite()
        for test in all_tests:
            rv.addTest(test)
        return rv


def setup_path():
    add_to_path(os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'test_apps')))


def suite():
    """A testsuite that has all the Flask tests.  You can use this
    function to integrate the Flask tests into your own testsuite
    in case you want to test that monkeypatches to Flask do not
    break it.
    """
    setup_path()
    suite = unittest.TestSuite()
    for other_suite in iter_suites():
        suite.addTest(other_suite)
    return suite


def main():
    """Runs the testsuite as command line application."""
    try:
        unittest.main(testLoader=BetterLoader(), defaultTest='suite')
    except Exception as e:
        print('Error: %s' % e)
