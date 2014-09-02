# -*- coding: utf-8 -*-
"""
    tests
    ~~~~~~~~~~~~~~~

    Tests Flask itself.  The majority of Flask is already tested
    as part of Werkzeug.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import print_function
import pytest

import os
import sys
import flask
import warnings
from functools import update_wrapper
from contextlib import contextmanager
from flask._compat import StringIO


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
            assert log, 'expected deprecation warning'
            for entry in log:
                assert 'Modules are deprecated' in str(entry['message'])
    return update_wrapper(new_f, f)


class TestFlask(object):
    """Baseclass for all the tests that Flask uses.  Use these methods
    for testing instead of the camelcased ones in the baseclass for
    consistency.
    """

    @pytest.fixture(autouse=True)
    def setup_path(self, monkeypatch):
        monkeypatch.syspath_prepend(
            os.path.abspath(os.path.join(
                os.path.dirname(__file__), 'test_apps'))
        )

    @pytest.fixture(autouse=True)
    def leak_detector(self, request):
        request.addfinalizer(self.ensure_clean_request_context)

    def ensure_clean_request_context(self):
        # make sure we're not leaking a request context since we are
        # testing flask internally in debug mode in a few cases
        leaks = []
        while flask._request_ctx_stack.top is not None:
            leaks.append(flask._request_ctx_stack.pop())
        assert leaks == []

    def setup_method(self, method):
        self.setup()

    def teardown_method(self, method):
        self.teardown()

    def setup(self):
        pass

    def teardown(self):
        pass
