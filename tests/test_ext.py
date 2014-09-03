# -*- coding: utf-8 -*-
"""
    tests.ext
    ~~~~~~~~~~~~~~~~~~~

    Tests the extension import thing.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import sys
import unittest
import pytest

try:
    from imp import reload as reload_module
except ImportError:
    reload_module = reload
from tests import TestFlask
from flask._compat import PY2


@pytest.fixture(autouse=True)
def importhook_setup(monkeypatch, request):
    # we clear this out for various reasons.  The most important one is
    # that a real flaskext could be in there which would disable our
    # fake package.  Secondly we want to make sure that the flaskext
    # import hook does not break on reloading.
    for entry, value in list(sys.modules.items()):
        if (entry.startswith('flask.ext.') or
            entry.startswith('flask_') or
            entry.startswith('flaskext.') or
            entry == 'flaskext') and value is not None:
            monkeypatch.delitem(sys.modules, entry)
    from flask import ext
    reload_module(ext)

    # reloading must not add more hooks
    import_hooks = 0
    for item in sys.meta_path:
        cls = type(item)
        if cls.__module__ == 'flask.exthook' and \
           cls.__name__ == 'ExtensionImporter':
            import_hooks += 1
    assert import_hooks == 1

    def teardown():
        from flask import ext
        for key in ext.__dict__:
            assert '.' not in key

    request.addfinalizer(teardown)

def test_flaskext_new_simple_import_normal():
    from flask.ext.newext_simple import ext_id
    assert ext_id == 'newext_simple'

def test_flaskext_new_simple_import_module():
    from flask.ext import newext_simple
    assert newext_simple.ext_id == 'newext_simple'
    assert newext_simple.__name__ == 'flask_newext_simple'

def test_flaskext_new_package_import_normal():
    from flask.ext.newext_package import ext_id
    assert ext_id == 'newext_package'

def test_flaskext_new_package_import_module():
    from flask.ext import newext_package
    assert newext_package.ext_id == 'newext_package'
    assert newext_package.__name__ == 'flask_newext_package'

def test_flaskext_new_package_import_submodule_function():
    from flask.ext.newext_package.submodule import test_function
    assert test_function() == 42

def test_flaskext_new_package_import_submodule():
    from flask.ext.newext_package import submodule
    assert submodule.__name__ == 'flask_newext_package.submodule'
    assert submodule.test_function() == 42

def test_flaskext_old_simple_import_normal():
    from flask.ext.oldext_simple import ext_id
    assert ext_id == 'oldext_simple'

def test_flaskext_old_simple_import_module():
    from flask.ext import oldext_simple
    assert oldext_simple.ext_id == 'oldext_simple'
    assert oldext_simple.__name__ == 'flaskext.oldext_simple'

def test_flaskext_old_package_import_normal():
    from flask.ext.oldext_package import ext_id
    assert ext_id == 'oldext_package'

def test_flaskext_old_package_import_module():
    from flask.ext import oldext_package
    assert oldext_package.ext_id == 'oldext_package'
    assert oldext_package.__name__ == 'flaskext.oldext_package'

def test_flaskext_old_package_import_submodule():
    from flask.ext.oldext_package import submodule
    assert submodule.__name__ == 'flaskext.oldext_package.submodule'
    assert submodule.test_function() == 42

def test_flaskext_old_package_import_submodule_function():
    from flask.ext.oldext_package.submodule import test_function
    assert test_function() == 42

def test_flaskext_broken_package_no_module_caching():
    for x in range(2):
        with pytest.raises(ImportError):
            import flask.ext.broken

def test_no_error_swallowing():
    try:
        import flask.ext.broken
    except ImportError:
        exc_type, exc_value, tb = sys.exc_info()
        assert exc_type is ImportError
        if PY2:
            message = 'No module named missing_module'
        else:
            message = 'No module named \'missing_module\''
        assert str(exc_value) == message
        assert tb.tb_frame.f_globals is globals()

        # reraise() adds a second frame so we need to skip that one too.
        # On PY3 we even have another one :(
        next = tb.tb_next.tb_next
        if not PY2:
            next = next.tb_next

        import os.path
        assert os.path.join('flask_broken', '__init__.py') in \
            next.tb_frame.f_code.co_filename
    else:
        1/0  # XXX
