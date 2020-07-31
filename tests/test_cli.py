# This file was part of Flask-CLI and was modified under the terms of
# its Revised BSD License. Copyright © 2015 CERN.
import os
import ssl
import sys
import types
from functools import partial

import click
import pytest
from _pytest.monkeypatch import notset
from click.testing import CliRunner

from flask import Blueprint
from flask import current_app
from flask import Flask
from flask.cli import AppGroup
from flask.cli import dotenv
from flask.cli import find_best_app
from flask.cli import FlaskGroup
from flask.cli import get_version
from flask.cli import load_dotenv
from flask.cli import locate_app
from flask.cli import NoAppException
from flask.cli import prepare_import
from flask.cli import run_command
from flask.cli import ScriptInfo
from flask.cli import with_appcontext

cwd = os.getcwd()
test_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "test_apps"))


@pytest.fixture
def runner():
    return CliRunner()


def test_cli_name(test_apps):
    """Make sure the CLI object's name is the app's name and not the app itself"""
    from cliapp.app import testapp

    assert testapp.cli.name == testapp.name


def test_find_best_app(test_apps):
    script_info = ScriptInfo()

    class Module:
        app = Flask("appname")

    assert find_best_app(script_info, Module) == Module.app

    class Module:
        application = Flask("appname")

    assert find_best_app(script_info, Module) == Module.application

    class Module:
        myapp = Flask("appname")

    assert find_best_app(script_info, Module) == Module.myapp

    class Module:
        @staticmethod
        def create_app():
            return Flask("appname")

    app = find_best_app(script_info, Module)
    assert isinstance(app, Flask)
    assert app.name == "appname"

    class Module:
        @staticmethod
        def create_app(foo):
            return Flask("appname")

    with pytest.deprecated_call(match="Script info"):
        app = find_best_app(script_info, Module)

    assert isinstance(app, Flask)
    assert app.name == "appname"

    class Module:
        @staticmethod
        def create_app(foo=None, script_info=None):
            return Flask("appname")

    with pytest.deprecated_call(match="script_info"):
        app = find_best_app(script_info, Module)

    assert isinstance(app, Flask)
    assert app.name == "appname"

    class Module:
        @staticmethod
        def make_app():
            return Flask("appname")

    app = find_best_app(script_info, Module)
    assert isinstance(app, Flask)
    assert app.name == "appname"

    class Module:
        myapp = Flask("appname1")

        @staticmethod
        def create_app():
            return Flask("appname2")

    assert find_best_app(script_info, Module) == Module.myapp

    class Module:
        myapp = Flask("appname1")

        @staticmethod
        def create_app():
            return Flask("appname2")

    assert find_best_app(script_info, Module) == Module.myapp

    class Module:
        pass

    pytest.raises(NoAppException, find_best_app, script_info, Module)

    class Module:
        myapp1 = Flask("appname1")
        myapp2 = Flask("appname2")

    pytest.raises(NoAppException, find_best_app, script_info, Module)

    class Module:
        @staticmethod
        def create_app(foo, bar):
            return Flask("appname2")

    pytest.raises(NoAppException, find_best_app, script_info, Module)

    class Module:
        @staticmethod
        def create_app():
            raise TypeError("bad bad factory!")

    pytest.raises(TypeError, find_best_app, script_info, Module)


@pytest.mark.parametrize(
    "value,path,result",
    (
        ("test", cwd, "test"),
        ("test.py", cwd, "test"),
        ("a/test", os.path.join(cwd, "a"), "test"),
        ("test/__init__.py", cwd, "test"),
        ("test/__init__", cwd, "test"),
        # nested package
        (
            os.path.join(test_path, "cliapp", "inner1", "__init__"),
            test_path,
            "cliapp.inner1",
        ),
        (
            os.path.join(test_path, "cliapp", "inner1", "inner2"),
            test_path,
            "cliapp.inner1.inner2",
        ),
        # dotted name
        ("test.a.b", cwd, "test.a.b"),
        (os.path.join(test_path, "cliapp.app"), test_path, "cliapp.app"),
        # not a Python file, will be caught during import
        (
            os.path.join(test_path, "cliapp", "message.txt"),
            test_path,
            "cliapp.message.txt",
        ),
    ),
)
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


@pytest.mark.parametrize(
    "iname,aname,result",
    (
        ("cliapp.app", None, "testapp"),
        ("cliapp.app", "testapp", "testapp"),
        ("cliapp.factory", None, "app"),
        ("cliapp.factory", "create_app", "app"),
        ("cliapp.factory", "create_app()", "app"),
        ("cliapp.factory", 'create_app2("foo", "bar")', "app2_foo_bar"),
        # trailing comma space
        ("cliapp.factory", 'create_app2("foo", "bar", )', "app2_foo_bar"),
        # strip whitespace
        ("cliapp.factory", " create_app () ", "app"),
    ),
)
def test_locate_app(test_apps, iname, aname, result):
    info = ScriptInfo()
    assert locate_app(info, iname, aname).name == result


@pytest.mark.parametrize(
    "iname,aname",
    (
        ("notanapp.py", None),
        ("cliapp/app", None),
        ("cliapp.app", "notanapp"),
        # not enough arguments
        ("cliapp.factory", 'create_app2("foo")'),
        # invalid identifier
        ("cliapp.factory", "create_app("),
        # no app returned
        ("cliapp.factory", "no_app"),
        # nested import error
        ("cliapp.importerrorapp", None),
        # not a Python file
        ("cliapp.message.txt", None),
    ),
)
def test_locate_app_raises(test_apps, iname, aname):
    info = ScriptInfo()

    with pytest.raises(NoAppException):
        locate_app(info, iname, aname)


def test_locate_app_suppress_raise(test_apps):
    info = ScriptInfo()
    app = locate_app(info, "notanapp.py", None, raise_if_not_found=False)
    assert app is None

    # only direct import error is suppressed
    with pytest.raises(NoAppException):
        locate_app(info, "cliapp.importerrorapp", None, raise_if_not_found=False)


def test_get_version(test_apps, capsys):
    from flask import __version__ as flask_version
    from werkzeug import __version__ as werkzeug_version
    from platform import python_version

    class MockCtx:
        resilient_parsing = False
        color = None

        def exit(self):
            return

    ctx = MockCtx()
    get_version(ctx, None, "test")
    out, err = capsys.readouterr()
    assert f"Python {python_version()}" in out
    assert f"Flask {flask_version}" in out
    assert f"Werkzeug {werkzeug_version}" in out


def test_scriptinfo(test_apps, monkeypatch):
    obj = ScriptInfo(app_import_path="cliapp.app:testapp")
    app = obj.load_app()
    assert app.name == "testapp"
    assert obj.load_app() is app

    # import app with module's absolute path
    cli_app_path = os.path.abspath(
        os.path.join(os.path.dirname(__file__), "test_apps", "cliapp", "app.py")
    )
    obj = ScriptInfo(app_import_path=cli_app_path)
    app = obj.load_app()
    assert app.name == "testapp"
    assert obj.load_app() is app
    obj = ScriptInfo(app_import_path=f"{cli_app_path}:testapp")
    app = obj.load_app()
    assert app.name == "testapp"
    assert obj.load_app() is app

    def create_app():
        return Flask("createapp")

    obj = ScriptInfo(create_app=create_app)
    app = obj.load_app()
    assert app.name == "createapp"
    assert obj.load_app() is app

    obj = ScriptInfo()
    pytest.raises(NoAppException, obj.load_app)

    # import app from wsgi.py in current directory
    monkeypatch.chdir(
        os.path.abspath(
            os.path.join(os.path.dirname(__file__), "test_apps", "helloworld")
        )
    )
    obj = ScriptInfo()
    app = obj.load_app()
    assert app.name == "hello"

    # import app from app.py in current directory
    monkeypatch.chdir(
        os.path.abspath(os.path.join(os.path.dirname(__file__), "test_apps", "cliapp"))
    )
    obj = ScriptInfo()
    app = obj.load_app()
    assert app.name == "testapp"


def test_with_appcontext(runner):
    @click.command()
    @with_appcontext
    def testcmd():
        click.echo(current_app.name)

    obj = ScriptInfo(create_app=lambda: Flask("testapp"))

    result = runner.invoke(testcmd, obj=obj)
    assert result.exit_code == 0
    assert result.output == "testapp\n"


def test_appgroup(runner):
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

    obj = ScriptInfo(create_app=lambda: Flask("testappgroup"))

    result = runner.invoke(cli, ["test"], obj=obj)
    assert result.exit_code == 0
    assert result.output == "testappgroup\n"

    result = runner.invoke(cli, ["subgroup", "test2"], obj=obj)
    assert result.exit_code == 0
    assert result.output == "testappgroup\n"


def test_flaskgroup(runner):
    def create_app():
        return Flask("flaskgroup")

    @click.group(cls=FlaskGroup, create_app=create_app)
    def cli(**params):
        pass

    @cli.command()
    def test():
        click.echo(current_app.name)

    result = runner.invoke(cli, ["test"])
    assert result.exit_code == 0
    assert result.output == "flaskgroup\n"


@pytest.mark.parametrize("set_debug_flag", (True, False))
def test_flaskgroup_debug(runner, set_debug_flag):
    def create_app():
        app = Flask("flaskgroup")
        app.debug = True
        return app

    @click.group(cls=FlaskGroup, create_app=create_app, set_debug_flag=set_debug_flag)
    def cli(**params):
        pass

    @cli.command()
    def test():
        click.echo(str(current_app.debug))

    result = runner.invoke(cli, ["test"])
    assert result.exit_code == 0
    assert result.output == f"{not set_debug_flag}\n"


def test_no_command_echo_loading_error():
    from flask.cli import cli

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli, ["missing"])
    assert result.exit_code == 2
    assert "FLASK_APP" in result.stderr
    assert "Usage:" in result.stderr


def test_help_echo_loading_error():
    from flask.cli import cli

    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "FLASK_APP" in result.stderr
    assert "Usage:" in result.stdout


def test_help_echo_exception():
    def create_app():
        raise Exception("oh no")

    cli = FlaskGroup(create_app=create_app)
    runner = CliRunner(mix_stderr=False)
    result = runner.invoke(cli, ["--help"])
    assert result.exit_code == 0
    assert "Exception: oh no" in result.stderr
    assert "Usage:" in result.stdout


class TestRoutes:
    @pytest.fixture
    def invoke(self, runner):
        def create_app():
            app = Flask(__name__)
            app.testing = True

            @app.route("/get_post/<int:x>/<int:y>", methods=["GET", "POST"])
            def yyy_get_post(x, y):
                pass

            @app.route("/zzz_post", methods=["POST"])
            def aaa_post():
                pass

            return app

        cli = FlaskGroup(create_app=create_app)
        return partial(runner.invoke, cli)

    @pytest.fixture
    def invoke_no_routes(self, runner):
        def create_app():
            app = Flask(__name__, static_folder=None)
            app.testing = True

            return app

        cli = FlaskGroup(create_app=create_app)
        return partial(runner.invoke, cli)

    def expect_order(self, order, output):
        # skip the header and match the start of each row
        for expect, line in zip(order, output.splitlines()[2:]):
            # do this instead of startswith for nicer pytest output
            assert line[: len(expect)] == expect

    def test_simple(self, invoke):
        result = invoke(["routes"])
        assert result.exit_code == 0
        self.expect_order(["aaa_post", "static", "yyy_get_post"], result.output)

    def test_sort(self, invoke):
        default_output = invoke(["routes"]).output
        endpoint_output = invoke(["routes", "-s", "endpoint"]).output
        assert default_output == endpoint_output
        self.expect_order(
            ["static", "yyy_get_post", "aaa_post"],
            invoke(["routes", "-s", "methods"]).output,
        )
        self.expect_order(
            ["yyy_get_post", "static", "aaa_post"],
            invoke(["routes", "-s", "rule"]).output,
        )
        self.expect_order(
            ["aaa_post", "yyy_get_post", "static"],
            invoke(["routes", "-s", "match"]).output,
        )

    def test_all_methods(self, invoke):
        output = invoke(["routes"]).output
        assert "GET, HEAD, OPTIONS, POST" not in output
        output = invoke(["routes", "--all-methods"]).output
        assert "GET, HEAD, OPTIONS, POST" in output

    def test_no_routes(self, invoke_no_routes):
        result = invoke_no_routes(["routes"])
        assert result.exit_code == 0
        assert "No routes were registered." in result.output


need_dotenv = pytest.mark.skipif(dotenv is None, reason="dotenv is not installed")


@need_dotenv
def test_load_dotenv(monkeypatch):
    # can't use monkeypatch.delitem since the keys don't exist yet
    for item in ("FOO", "BAR", "SPAM"):
        monkeypatch._setitem.append((os.environ, item, notset))

    monkeypatch.setenv("EGGS", "3")
    monkeypatch.chdir(test_path)
    assert load_dotenv()
    assert os.getcwd() == test_path
    # .flaskenv doesn't overwrite .env
    assert os.environ["FOO"] == "env"
    # set only in .flaskenv
    assert os.environ["BAR"] == "bar"
    # set only in .env
    assert os.environ["SPAM"] == "1"
    # set manually, files don't overwrite
    assert os.environ["EGGS"] == "3"

    # Non existent file should not load
    assert not load_dotenv("non-existent-file")


@need_dotenv
def test_dotenv_path(monkeypatch):
    for item in ("FOO", "BAR", "EGGS"):
        monkeypatch._setitem.append((os.environ, item, notset))

    cwd = os.getcwd()
    load_dotenv(os.path.join(test_path, ".flaskenv"))
    assert os.getcwd() == cwd
    assert "FOO" in os.environ


def test_dotenv_optional(monkeypatch):
    monkeypatch.setattr("flask.cli.dotenv", None)
    monkeypatch.chdir(test_path)
    load_dotenv()
    assert "FOO" not in os.environ


@need_dotenv
def test_disable_dotenv_from_env(monkeypatch, runner):
    monkeypatch.chdir(test_path)
    monkeypatch.setitem(os.environ, "FLASK_SKIP_DOTENV", "1")
    runner.invoke(FlaskGroup())
    assert "FOO" not in os.environ


def test_run_cert_path():
    # no key
    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--cert", __file__])

    # no cert
    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--key", __file__])

    ctx = run_command.make_context("run", ["--cert", __file__, "--key", __file__])
    assert ctx.params["cert"] == (__file__, __file__)


def test_run_cert_adhoc(monkeypatch):
    monkeypatch.setitem(sys.modules, "cryptography", None)

    # cryptography not installed
    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--cert", "adhoc"])

    # cryptography installed
    monkeypatch.setitem(sys.modules, "cryptography", types.ModuleType("cryptography"))
    ctx = run_command.make_context("run", ["--cert", "adhoc"])
    assert ctx.params["cert"] == "adhoc"

    # no key with adhoc
    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--cert", "adhoc", "--key", __file__])


def test_run_cert_import(monkeypatch):
    monkeypatch.setitem(sys.modules, "not_here", None)

    # ImportError
    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--cert", "not_here"])

    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--cert", "flask"])

    # SSLContext
    ssl_context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)

    monkeypatch.setitem(sys.modules, "ssl_context", ssl_context)
    ctx = run_command.make_context("run", ["--cert", "ssl_context"])
    assert ctx.params["cert"] is ssl_context

    # no --key with SSLContext
    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--cert", "ssl_context", "--key", __file__])


def test_run_cert_no_ssl(monkeypatch):
    monkeypatch.setattr("flask.cli.ssl", None)
    with pytest.raises(click.BadParameter):
        run_command.make_context("run", ["--cert", "not_here"])


def test_cli_blueprints(app):
    """Test blueprint commands register correctly to the application"""
    custom = Blueprint("custom", __name__, cli_group="customized")
    nested = Blueprint("nested", __name__)
    merged = Blueprint("merged", __name__, cli_group=None)
    late = Blueprint("late", __name__)

    @custom.cli.command("custom")
    def custom_command():
        click.echo("custom_result")

    @nested.cli.command("nested")
    def nested_command():
        click.echo("nested_result")

    @merged.cli.command("merged")
    def merged_command():
        click.echo("merged_result")

    @late.cli.command("late")
    def late_command():
        click.echo("late_result")

    app.register_blueprint(custom)
    app.register_blueprint(nested)
    app.register_blueprint(merged)
    app.register_blueprint(late, cli_group="late_registration")

    app_runner = app.test_cli_runner()

    result = app_runner.invoke(args=["customized", "custom"])
    assert "custom_result" in result.output

    result = app_runner.invoke(args=["nested", "nested"])
    assert "nested_result" in result.output

    result = app_runner.invoke(args=["merged"])
    assert "merged_result" in result.output

    result = app_runner.invoke(args=["late_registration", "late"])
    assert "late_result" in result.output


def test_cli_empty(app):
    """If a Blueprint's CLI group is empty, do not register it."""
    bp = Blueprint("blue", __name__, cli_group="blue")
    app.register_blueprint(bp)

    result = app.test_cli_runner().invoke(args=["blue", "--help"])
    assert result.exit_code == 2, f"Unexpected success:\n\n{result.output}"
