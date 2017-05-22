# -*- coding: utf-8 -*-
"""
    tests.test_cli
    ~~~~~~~~~~~~~~

    :copyright: (c) 2016 by the Flask Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
#
# This file was part of Flask-CLI and was modified under the terms its license,
# the Revised BSD License.
# Copyright (C) 2015 CERN.
#
from __future__ import absolute_import, print_function
import os
import sys
from functools import partial

import click
import pytest
from click.testing import CliRunner
from flask import Flask, current_app

from flask.cli import cli, AppGroup, FlaskGroup, NoAppException, ScriptInfo, \
    find_best_app, locate_app, with_appcontext, prepare_exec_for_file, \
    find_default_import_path, get_version


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_name(test_apps):
    """Make sure the CLI object's name is the app's name and not the app itself"""
    from cliapp.app import testapp
    assert testapp.cli.name == testapp.name


def test_find_best_app(test_apps):
    """Test if `find_best_app` behaves as expected with different combinations of input."""
    class Module:
        app = Flask('appname')
    assert find_best_app(Module) == Module.app

    class Module:
        application = Flask('appname')
    assert find_best_app(Module) == Module.application

    class Module:
        myapp = Flask('appname')
    assert find_best_app(Module) == Module.myapp

    class Module:
        pass
    pytest.raises(NoAppException, find_best_app, Module)

    class Module:
        myapp1 = Flask('appname1')
        myapp2 = Flask('appname2')
    pytest.raises(NoAppException, find_best_app, Module)


def test_prepare_exec_for_file(test_apps):
    """Expect the correct path to be set and the correct module name to be returned.

    :func:`prepare_exec_for_file` has a side effect, where
    the parent directory of given file is added to `sys.path`.
    """
    realpath = os.path.realpath('/tmp/share/test.py')
    dirname = os.path.dirname(realpath)
    assert prepare_exec_for_file('/tmp/share/test.py') == 'test'
    assert dirname in sys.path

    realpath = os.path.realpath('/tmp/share/__init__.py')
    dirname = os.path.dirname(os.path.dirname(realpath))
    assert prepare_exec_for_file('/tmp/share/__init__.py') == 'share'
    assert dirname in sys.path

    with pytest.raises(NoAppException):
        prepare_exec_for_file('/tmp/share/test.txt')


def test_locate_app(test_apps):
    """Test of locate_app."""
    assert locate_app("cliapp.app").name == "testapp"
    assert locate_app("cliapp.app:testapp").name == "testapp"
    assert locate_app("cliapp.multiapp:app1").name == "app1"
    pytest.raises(NoAppException, locate_app, "notanpp.py")
    pytest.raises(NoAppException, locate_app, "cliapp/app")
    pytest.raises(RuntimeError, locate_app, "cliapp.app:notanapp")
    pytest.raises(NoAppException, locate_app, "cliapp.importerrorapp")


def test_find_default_import_path(test_apps, monkeypatch, tmpdir):
    """Test of find_default_import_path."""
    monkeypatch.delitem(os.environ, 'FLASK_APP', raising=False)
    assert find_default_import_path() == None
    monkeypatch.setitem(os.environ, 'FLASK_APP', 'notanapp')
    assert find_default_import_path() == 'notanapp'
    tmpfile = tmpdir.join('testapp.py')
    tmpfile.write('')
    monkeypatch.setitem(os.environ, 'FLASK_APP', str(tmpfile))
    expect_rv = prepare_exec_for_file(str(tmpfile))
    assert find_default_import_path() == expect_rv


def test_get_version(test_apps, capsys):
    """Test of get_version."""
    from flask import __version__ as flask_ver
    from sys import version as py_ver
    class MockCtx(object):
        resilient_parsing = False
        color = None
        def exit(self): return
    ctx = MockCtx()
    get_version(ctx, None, "test")
    out, err = capsys.readouterr()
    assert flask_ver in out
    assert py_ver in out


def test_scriptinfo(test_apps):
    """Test of ScriptInfo."""
    obj = ScriptInfo(app_import_path="cliapp.app:testapp")
    assert obj.load_app().name == "testapp"
    assert obj.load_app().name == "testapp"

    def create_app(info):
        return Flask("createapp")

    obj = ScriptInfo(create_app=create_app)
    app = obj.load_app()
    assert app.name == "createapp"
    assert obj.load_app() == app


def test_with_appcontext(runner):
    """Test of with_appcontext."""
    @click.command()
    @with_appcontext
    def testcmd():
        click.echo(current_app.name)

    obj = ScriptInfo(create_app=lambda info: Flask("testapp"))

    result = runner.invoke(testcmd, obj=obj)
    assert result.exit_code == 0
    assert result.output == 'testapp\n'


def test_appgroup(runner):
    """Test of with_appcontext."""
    @click.group(cls=AppGroup)
    def cli():
        pass

    @cli.command(with_appcontext=True)
    def test():
        click.echo(current_app.name)

    @cli.group()
    def subgroup():
        pass

    @subgroup.command(with_appcontext=True)
    def test2():
        click.echo(current_app.name)

    obj = ScriptInfo(create_app=lambda info: Flask("testappgroup"))

    result = runner.invoke(cli, ['test'], obj=obj)
    assert result.exit_code == 0
    assert result.output == 'testappgroup\n'

    result = runner.invoke(cli, ['subgroup', 'test2'], obj=obj)
    assert result.exit_code == 0
    assert result.output == 'testappgroup\n'


def test_flaskgroup(runner):
    """Test FlaskGroup."""
    def create_app(info):
        return Flask("flaskgroup")

    @click.group(cls=FlaskGroup, create_app=create_app)
    def cli(**params):
        pass

    @cli.command()
    def test():
        click.echo(current_app.name)

    result = runner.invoke(cli, ['test'])
    assert result.exit_code == 0
    assert result.output == 'flaskgroup\n'


def test_print_exceptions(runner):
    """Print the stacktrace if the CLI."""
    def create_app(info):
        raise Exception("oh no")
        return Flask("flaskgroup")

    @click.group(cls=FlaskGroup, create_app=create_app)
    def cli(**params):
        pass

    result = runner.invoke(cli, ['--help'])
    assert result.exit_code == 0
    assert 'Exception: oh no' in result.output
    assert 'Traceback' in result.output


class TestRoutes:
    @pytest.fixture
    def invoke(self, runner):
        def create_app(info):
            app = Flask(__name__)
            app.testing = True

            @app.route('/get_post/<int:x>/<int:y>', methods=['GET', 'POST'])
            def yyy_get_post(x, y):
                pass

            @app.route('/zzz_post', methods=['POST'])
            def aaa_post():
                pass

            return app

        cli = FlaskGroup(create_app=create_app)
        return partial(runner.invoke, cli)

    def expect_order(self, order, output):
        # skip the header and match the start of each row
        for expect, line in zip(order, output.splitlines()[2:]):
            # do this instead of startswith for nicer pytest output
            assert line[:len(expect)] == expect

    def test_simple(self, invoke):
        result = invoke(['routes'])
        assert result.exit_code == 0
        self.expect_order(
            ['aaa_post', 'static', 'yyy_get_post'],
            result.output
        )

    def test_sort(self, invoke):
        default_output = invoke(['routes']).output
        endpoint_output = invoke(['routes', '-s', 'endpoint']).output
        assert default_output == endpoint_output
        self.expect_order(
            ['static', 'yyy_get_post', 'aaa_post'],
            invoke(['routes', '-s', 'methods']).output
        )
        self.expect_order(
            ['yyy_get_post', 'static', 'aaa_post'],
            invoke(['routes', '-s', 'rule']).output
        )
        self.expect_order(
            ['aaa_post', 'yyy_get_post', 'static'],
            invoke(['routes', '-s', 'match']).output
        )

    def test_all_methods(self, invoke):
        output = invoke(['routes']).output
        assert 'GET, HEAD, OPTIONS, POST' not in output
        output = invoke(['routes', '--all-methods']).output
        assert 'GET, HEAD, OPTIONS, POST' in output
