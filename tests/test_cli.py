# -*- coding: utf-8 -*-
"""
    tests.test_cli
    ~~~~~~~~~~~~~~

    :copyright: © 2010 by the Pallets team.
    :license: BSD, see LICENSE for more details.
"""

# This file was part of Flask-CLI and was modified under the terms of
# its Revised BSD License. Copyright © 2015 CERN.

from __future__ import absolute_import

import os
import ssl
import sys
import types
from functools import partial

import click
import pytest
from _pytest.monkeypatch import notset
from click.testing import CliRunner

from flask import Flask, current_app
from flask.cli import (
    AppGroup, FlaskGroup, NoAppException, ScriptInfo, dotenv, find_best_app,
    get_version, load_dotenv, locate_app, prepare_import, run_command,
    with_appcontext
)

cwd = os.getcwd()
test_path = os.path.abspath(os.path.join(
    os.path.dirname(__file__), 'test_apps'
))


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_name(test_apps):
    """Make sure the CLI object's name is the app's name and not the app itself"""
    from cliapp.app import testapp
    assert testapp.cli.name == testapp.name


def test_find_best_app(test_apps):
    """Test if `find_best_app` behaves as expected with different combinations of input."""
    script_info = ScriptInfo()

    class Module:
        app = Flask('appname')

    assert find_best_app(script_info, Module) == Module.app

    class Module:
        application = Flask('appname')

    assert find_best_app(script_info, Module) == Module.application

    class Module:
        myapp = Flask('appname')

    assert find_best_app(script_info, Module) == Module.myapp

    class Module:
        @staticmethod
        def create_app():
            return Flask('appname')

    assert isinstance(find_best_app(script_info, Module), Flask)
    assert find_best_app(script_info, Module).name == 'appname'

    class Module:
        @staticmethod
        def create_app(foo):
            return Flask('appname')

    assert isinstance(find_best_app(script_info, Module), Flask)
    assert find_best_app(script_info, Module).name == 'appname'

    class Module:
        @staticmethod
        def create_app(foo=None, script_info=None):
            return Flask('appname')

    assert isinstance(find_best_app(script_info, Module), Flask)
    assert find_best_app(script_info, Module).name == 'appname'

    class Module:
        @staticmethod
        def make_app():
            return Flask('appname')

    assert isinstance(find_best_app(script_info, Module), Flask)
    assert find_best_app(script_info, Module).name == 'appname'

    class Module:
        myapp = Flask('appname1')

        @staticmethod
        def create_app():
            return Flask('appname2')

    assert find_best_app(script_info, Module) == Module.myapp

    class Module:
        myapp = Flask('appname1')

        @staticmethod
        def create_app():
            return Flask('appname2')

    assert find_best_app(script_info, Module) == Module.myapp

    class Module:
        pass

    pytest.raises(NoAppException, find_best_app, script_info, Module)

    class Module:
        myapp1 = Flask('appname1')
        myapp2 = Flask('appname2')

    pytest.raises(NoAppException, find_best_app, script_info, Module)

    class Module:
        @staticmethod
        def create_app(foo, bar):
            return Flask('appname2')

    pytest.raises(NoAppException, find_best_app, script_info, Module)

    class Module:
        @staticmethod
        def create_app():
            raise TypeError('bad bad factory!')

    pytest.raises(TypeError, find_best_app, script_info, Module)


@pytest.mark.parametrize('value,path,result', (
    ('test', cwd, 'test'),
    ('test.py', cwd, 'test'),
    ('a/test', os.path.join(cwd, 'a'), 'test'),
    ('test/__init__.py', cwd, 'test'),
    ('test/__init__', cwd, 'test'),
    # nested package
    (
        os.path.join(test_path, 'cliapp', 'inner1', '__init__'),
        test_path, 'cliapp.inner1'
    ),
    (
        os.path.join(test_path, 'cliapp', 'inner1', 'inner2'),
        test_path, 'cliapp.inner1.inner2'
    ),
    # dotted name
    ('test.a.b', cwd, 'test.a.b'),
    (os.path.join(test_path, 'cliapp.app'), test_path, 'cliapp.app'),
    # not a Python file, will be caught during import
    (
        os.path.join(test_path, 'cliapp', 'message.txt'),
        test_path, 'cliapp.message.txt'
    ),
))
def test_prepare_import(request, value, path, result):
    """Expect the correct path to be set and the correct import and app names
    to be returned.

    :func:`prepare_exec_for_file` has a side effect where the parent directory
    of the given import is added to :data:`sys.path`. This is reset after the
    test runs.
    """
    original_path = sys.path[:]

    def reset_path():
        sys.path[:] = original_path

    request.addfinalizer(reset_path)

    assert prepare_import(value) == result
    assert sys.path[0] == path


@pytest.mark.parametrize('iname,aname,result', (
    ('cliapp.app', None, 'testapp'),
    ('cliapp.app', 'testapp', 'testapp'),
    ('cliapp.factory', None, 'app'),
    ('cliapp.factory', 'create_app', 'app'),
    ('cliapp.factory', 'create_app()', 'app'),
    # no script_info
    ('cliapp.factory', 'create_app2("foo", "bar")', 'app2_foo_bar'),
    # trailing comma space
    ('cliapp.factory', 'create_app2("foo", "bar", )', 'app2_foo_bar'),
    # takes script_info
    ('cliapp.factory', 'create_app3("foo")', 'app3_foo_spam'),
    # strip whitespace
    ('cliapp.factory', ' create_app () ', 'app'),
))
def test_locate_app(test_apps, iname, aname, result):
    info = ScriptInfo()
    info.data['test'] = 'spam'
    assert locate_app(info, iname, aname).name == result


@pytest.mark.parametrize('iname,aname', (
    ('notanapp.py', None),
    ('cliapp/app', None),
    ('cliapp.app', 'notanapp'),
    # not enough arguments
    ('cliapp.factory', 'create_app2("foo")'),
    # invalid identifier
    ('cliapp.factory', 'create_app('),
    # no app returned
    ('cliapp.factory', 'no_app'),
    # nested import error
    ('cliapp.importerrorapp', None),
    # not a Python file
    ('cliapp.message.txt', None),
))
def test_locate_app_raises(test_apps, iname, aname):
    info = ScriptInfo()

    with pytest.raises(NoAppException):
        locate_app(info, iname, aname)


def test_locate_app_suppress_raise():
    info = ScriptInfo()
    app = locate_app(info, 'notanapp.py', None, raise_if_not_found=False)
    assert app is None

    # only direct import error is suppressed
    with pytest.raises(NoAppException):
        locate_app(
            info, 'cliapp.importerrorapp', None, raise_if_not_found=False
        )


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


def test_scriptinfo(test_apps, monkeypatch):
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

    obj = ScriptInfo()
    pytest.raises(NoAppException, obj.load_app)

    # import app from wsgi.py in current directory
    monkeypatch.chdir(os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'test_apps', 'helloworld'
    )))
    obj = ScriptInfo()
    app = obj.load_app()
    assert app.name == 'hello'

    # import app from app.py in current directory
    monkeypatch.chdir(os.path.abspath(os.path.join(
        os.path.dirname(__file__), 'test_apps', 'cliapp'
    )))
    obj = ScriptInfo()
    app = obj.load_app()
    assert app.name == 'testapp'


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


@pytest.mark.parametrize('set_debug_flag', (True, False))
def test_flaskgroup_debug(runner, set_debug_flag):
    """Test FlaskGroup debug flag behavior."""

    def create_app(info):
        app = Flask("flaskgroup")
        app.debug = True
        return app

    @click.group(cls=FlaskGroup, create_app=create_app, set_debug_flag=set_debug_flag)
    def cli(**params):
        pass

    @cli.command()
    def test():
        click.echo(str(current_app.debug))

    result = runner.invoke(cli, ['test'])
    assert result.exit_code == 0
    assert result.output == '%s\n' % str(not set_debug_flag)


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

    @pytest.fixture
    def invoke_no_routes(self, runner):
        def create_app(info):
            app = Flask(__name__, static_folder=None)
            app.testing = True

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

    def test_no_routes(self, invoke_no_routes):
        result = invoke_no_routes(['routes'])
        assert result.exit_code == 0
        assert 'No routes were registered.' in result.output


need_dotenv = pytest.mark.skipif(
    dotenv is None, reason='dotenv is not installed'
)


@need_dotenv
def test_load_dotenv(monkeypatch):
    # can't use monkeypatch.delitem since the keys don't exist yet
    for item in ('FOO', 'BAR', 'SPAM'):
        monkeypatch._setitem.append((os.environ, item, notset))

    monkeypatch.setenv('EGGS', '3')
    monkeypatch.chdir(os.path.join(test_path, 'cliapp', 'inner1'))
    load_dotenv()
    assert os.getcwd() == test_path
    # .flaskenv doesn't overwrite .env
    assert os.environ['FOO'] == 'env'
    # set only in .flaskenv
    assert os.environ['BAR'] == 'bar'
    # set only in .env
    assert os.environ['SPAM'] == '1'
    # set manually, files don't overwrite
    assert os.environ['EGGS'] == '3'


@need_dotenv
def test_dotenv_path(monkeypatch):
    for item in ('FOO', 'BAR', 'EGGS'):
        monkeypatch._setitem.append((os.environ, item, notset))

    cwd = os.getcwd()
    load_dotenv(os.path.join(test_path, '.flaskenv'))
    assert os.getcwd() == cwd
    assert 'FOO' in os.environ


def test_dotenv_optional(monkeypatch):
    monkeypatch.setattr('flask.cli.dotenv', None)
    monkeypatch.chdir(test_path)
    load_dotenv()
    assert 'FOO' not in os.environ


@need_dotenv
def test_disable_dotenv_from_env(monkeypatch, runner):
    monkeypatch.chdir(test_path)
    monkeypatch.setitem(os.environ, 'FLASK_SKIP_DOTENV', '1')
    runner.invoke(FlaskGroup())
    assert 'FOO' not in os.environ


def test_run_cert_path():
    # no key
    with pytest.raises(click.BadParameter):
        run_command.make_context('run', ['--cert', __file__])

    # no cert
    with pytest.raises(click.BadParameter):
        run_command.make_context('run', ['--key', __file__])

    ctx = run_command.make_context(
        'run', ['--cert', __file__, '--key', __file__])
    assert ctx.params['cert'] == (__file__, __file__)


def test_run_cert_adhoc(monkeypatch):
    monkeypatch.setitem(sys.modules, 'OpenSSL', None)

    # pyOpenSSL not installed
    with pytest.raises(click.BadParameter):
        run_command.make_context('run', ['--cert', 'adhoc'])

    # pyOpenSSL installed
    monkeypatch.setitem(sys.modules, 'OpenSSL', types.ModuleType('OpenSSL'))
    ctx = run_command.make_context('run', ['--cert', 'adhoc'])
    assert ctx.params['cert'] == 'adhoc'

    # no key with adhoc
    with pytest.raises(click.BadParameter):
        run_command.make_context('run', ['--cert', 'adhoc', '--key', __file__])


def test_run_cert_import(monkeypatch):
    monkeypatch.setitem(sys.modules, 'not_here', None)

    # ImportError
    with pytest.raises(click.BadParameter):
        run_command.make_context('run', ['--cert', 'not_here'])

    # not an SSLContext
    if sys.version_info >= (2, 7, 9):
        with pytest.raises(click.BadParameter):
            run_command.make_context('run', ['--cert', 'flask'])

    # SSLContext
    if sys.version_info < (2, 7, 9):
        ssl_context = object()
    else:
        ssl_context = ssl.SSLContext(ssl.PROTOCOL_SSLv23)

    monkeypatch.setitem(sys.modules, 'ssl_context', ssl_context)
    ctx = run_command.make_context('run', ['--cert', 'ssl_context'])
    assert ctx.params['cert'] is ssl_context

    # no --key with SSLContext
    with pytest.raises(click.BadParameter):
        run_command.make_context(
            'run', ['--cert', 'ssl_context', '--key', __file__])
