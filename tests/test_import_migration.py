# Tester for the flaskext_migrate.py module located in flask/scripts/
#
# Author: Keyan Pishdadian
import sys
sys.path.append('scripts')
import pytest
from redbaron import RedBaron
import flaskext_migrate as migrate


def test_simple_from_import():
    red = RedBaron("from flask.ext import foo")
    output = migrate.fix(red)
    assert output == "import flask_foo as foo"


def test_from_to_from_import():
    red = RedBaron("from flask.ext.foo import bar")
    output = migrate.fix(red)
    assert output == "from flask_foo import bar as bar"


def test_multiple_import():
    red = RedBaron("from flask.ext.foo import bar, foobar, something")
    output = migrate.fix(red)
    assert output == "from flask_foo import bar,foobar,something"


def test_multiline_import():
    red = RedBaron("from flask.ext.foo import \
                    bar,\
                    foobar,\
                    something")
    output = migrate.fix(red)
    assert output == "from flask_foo import bar,foobar,something"


def test_module_import():
    red = RedBaron("import flask.ext.foo")
    output = migrate.fix(red)
    assert output == "import flask_foo"


def test_module_import():
    red = RedBaron("from flask.ext.foo import bar as baz")
    output = migrate.fix(red)
    assert output == "from flask_foo import bar as baz"
