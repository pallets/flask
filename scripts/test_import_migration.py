# Tester for the flaskext_migrate.py module located in flask/scripts/
#
# Author: Keyan Pishdadian
import pytest
from redbaron import RedBaron
import flaskext_migrate as migrate


def test_simple_from_import():
    red = RedBaron("from flask.ext import foo")
    output = migrate.fix_tester(red)
    assert output == "import flask_foo as foo"


def test_from_to_from_import():
    red = RedBaron("from flask.ext.foo import bar")
    output = migrate.fix_tester(red)
    assert output == "from flask_foo import bar as bar"


def test_multiple_import():
    red = RedBaron("from flask.ext.foo import bar, foobar, something")
    output = migrate.fix_tester(red)
    assert output == "from flask_foo import bar, foobar, something"


def test_multiline_import():
    red = RedBaron("from flask.ext.foo import \
                    bar,\
                    foobar,\
                    something")
    output = migrate.fix_tester(red)
    assert output == "from flask_foo import bar, foobar, something"


def test_module_import():
    red = RedBaron("import flask.ext.foo")
    output = migrate.fix_tester(red)
    assert output == "import flask_foo"


def test_named_module_import():
    red = RedBaron("import flask.ext.foo as foobar")
    output = migrate.fix_tester(red)
    assert output == "import flask_foo as foobar"


def test_named_from_import():
    red = RedBaron("from flask.ext.foo import bar as baz")
    output = migrate.fix_tester(red)
    assert output == "from flask_foo import bar as baz"


def test_parens_import():
    red = RedBaron("from flask.ext.foo import (bar, foo, foobar)")
    output = migrate.fix_tester(red)
    assert output == "from flask_foo import (bar, foo, foobar)"


def test_function_call_migration():
    red = RedBaron("flask.ext.foo(var)")
    output = migrate.fix_tester(red)
    assert output == "flask_foo(var)"


def test_nested_function_call_migration():
    red = RedBaron("import flask.ext.foo\n\n"
                   "flask.ext.foo.bar(var)")
    output = migrate.fix_tester(red)
    assert output == ("import flask_foo\n\n"
                      "flask_foo.bar(var)")


def test_no_change_to_import():
    red = RedBaron("from flask import Flask")
    output = migrate.fix_tester(red)
    assert output == "from flask import Flask"
