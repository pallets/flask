# -*- coding: utf-8 -*-
"""
    flask.cli
    ~~~~~~~~~

    A simple command line application to run flask apps.

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import print_function

import ast
import inspect
import os
import re
import sys
import traceback
from functools import update_wrapper
from operator import attrgetter
from threading import Lock, Thread

import click

from . import __version__
from ._compat import getargspec, iteritems, reraise
from .globals import current_app
from .helpers import get_debug_flag

try:
    import dotenv
except ImportError:
    dotenv = None


class NoAppException(click.UsageError):
    """Raised if an application cannot be found or loaded."""


def find_best_app(script_info, module):
    """Given a module instance this tries to find the best possible
    application in the module or raises an exception.
    """
    from . import Flask

    # Search for the most common names first.
    for attr_name in ('app', 'application'):
        app = getattr(module, attr_name, None)
        if isinstance(app, Flask):
            return app

    # Otherwise find the only object that is a Flask instance.
    matches = [
        v for k, v in iteritems(module.__dict__) if isinstance(v, Flask)
    ]

    if len(matches) == 1:
        return matches[0]
    elif len(matches) > 1:
        raise NoAppException(
            'Auto-detected multiple Flask applications in module "{module}".'
            ' Use "FLASK_APP={module}:name" to specify the correct'
            ' one.'.format(module=module.__name__)
        )

    # Search for app factory functions.
    for attr_name in ('create_app', 'make_app'):
        app_factory = getattr(module, attr_name, None)

        if inspect.isfunction(app_factory):
            try:
                app = call_factory(app_factory, script_info)
                if isinstance(app, Flask):
                    return app
            except TypeError:
                raise NoAppException(
                    'Auto-detected "{function}()" in module "{module}", but '
                    'could not call it without specifying arguments.'.format(
                        function=attr_name, module=module.__name__
                    )
                )

    raise NoAppException(
        'Failed to find application in module "{module}". Are you sure '
        'it contains a Flask application? Maybe you wrapped it in a WSGI '
        'middleware.'.format(module=module.__name__)
    )


def call_factory(app_factory, script_info, arguments=()):
    """Takes an app factory, a ``script_info` object and  optionally a tuple
    of arguments. Checks for the existence of a script_info argument and calls
    the app_factory depending on that and the arguments provided.
    """
    args_spec = getargspec(app_factory)
    arg_names = args_spec.args
    arg_defaults = args_spec.defaults

    if 'script_info' in arg_names:
        return app_factory(*arguments, script_info=script_info)
    elif arguments:
        return app_factory(*arguments)
    elif not arguments and len(arg_names) == 1 and arg_defaults is None:
        return app_factory(script_info)
    return app_factory()


def find_app_by_string(string, script_info, module):
    """Checks if the given string is a variable name or a function. If it is
    a function, it checks for specified arguments and whether it takes
    a ``script_info`` argument and calls the function with the appropriate
    arguments."""
    from . import Flask
    function_regex = r'^(?P<name>\w+)(?:\((?P<args>.*)\))?$'
    match = re.match(function_regex, string)
    if match:
        name, args = match.groups()
        try:
            if args is not None:
                args = args.rstrip(' ,')
                if args:
                    args = ast.literal_eval(
                        "({args}, )".format(args=args))
                else:
                    args = ()
                app_factory = getattr(module, name, None)
                app = call_factory(app_factory, script_info, args)
            else:
                attr = getattr(module, name, None)
                if inspect.isfunction(attr):
                    app = call_factory(attr, script_info)
                else:
                    app = attr

            if isinstance(app, Flask):
                return app
            else:
                raise NoAppException('Failed to find application in module '
                                   '"{name}"'.format(name=module))
        except TypeError as e:
            new_error = NoAppException(
                '{e}\nThe app factory "{factory}" in module "{module}" could'
                ' not be called with the specified arguments (and a'
                ' script_info argument automatically added if applicable).'
                ' Did you make sure to use the right number of arguments as'
                ' well as not using keyword arguments or'
                ' non-literals?'.format(e=e, factory=string, module=module))
            reraise(NoAppException, new_error, sys.exc_info()[2])
    else:
        raise NoAppException(
            'The provided string "{string}" is not a valid variable name'
            'or function expression.'.format(string=string))


def prepare_import(path):
    """Given a filename this will try to calculate the python path, add it
    to the search path and return the actual module name that is expected.
    """
    path = os.path.realpath(path)

    if os.path.splitext(path)[1] == '.py':
        path = os.path.splitext(path)[0]

    if os.path.basename(path) == '__init__':
        path = os.path.dirname(path)

    module_name = []

    # move up until outside package structure (no __init__.py)
    while True:
        path, name = os.path.split(path)
        module_name.append(name)

        if not os.path.exists(os.path.join(path, '__init__.py')):
            break

    if sys.path[0] != path:
        sys.path.insert(0, path)

    return '.'.join(module_name[::-1])


def locate_app(script_info, module_name, app_name, raise_if_not_found=True):
    """Attempts to locate the application."""
    __traceback_hide__ = True

    try:
        __import__(module_name)
    except ImportError:
        # Reraise the ImportError if it occurred within the imported module.
        # Determine this by checking whether the trace has a depth > 1.
        if sys.exc_info()[-1].tb_next:
            raise NoAppException(
                'While importing "{name}", an ImportError was raised:'
                '\n\n{tb}'.format(name=module_name, tb=traceback.format_exc())
            )
        elif raise_if_not_found:
            raise NoAppException(
                'Could not import "{name}"."'.format(name=module_name)
            )
        else:
            return

    module = sys.modules[module_name]

    if app_name is None:
        return find_best_app(script_info, module)
    else:
        return find_app_by_string(app_name, script_info, module)


def get_version(ctx, param, value):
    if not value or ctx.resilient_parsing:
        return
    message = 'Flask %(version)s\nPython %(python_version)s'
    click.echo(message % {
        'version': __version__,
        'python_version': sys.version,
    }, color=ctx.color)
    ctx.exit()

version_option = click.Option(['--version'],
                              help='Show the flask version',
                              expose_value=False,
                              callback=get_version,
                              is_flag=True, is_eager=True)

class DispatchingApp(object):
    """Special application that dispatches to a Flask application which
    is imported by name in a background thread.  If an error happens
    it is recorded and shown as part of the WSGI handling which in case
    of the Werkzeug debugger means that it shows up in the browser.
    """

    def __init__(self, loader, use_eager_loading=False):
        self.loader = loader
        self._app = None
        self._lock = Lock()
        self._bg_loading_exc_info = None
        if use_eager_loading:
            self._load_unlocked()
        else:
            self._load_in_background()

    def _load_in_background(self):
        def _load_app():
            __traceback_hide__ = True
            with self._lock:
                try:
                    self._load_unlocked()
                except Exception:
                    self._bg_loading_exc_info = sys.exc_info()
        t = Thread(target=_load_app, args=())
        t.start()

    def _flush_bg_loading_exception(self):
        __traceback_hide__ = True
        exc_info = self._bg_loading_exc_info
        if exc_info is not None:
            self._bg_loading_exc_info = None
            reraise(*exc_info)

    def _load_unlocked(self):
        __traceback_hide__ = True
        self._app = rv = self.loader()
        self._bg_loading_exc_info = None
        return rv

    def __call__(self, environ, start_response):
        __traceback_hide__ = True
        if self._app is not None:
            return self._app(environ, start_response)
        self._flush_bg_loading_exception()
        with self._lock:
            if self._app is not None:
                rv = self._app
            else:
                rv = self._load_unlocked()
            return rv(environ, start_response)


class ScriptInfo(object):
    """Help object to deal with Flask applications.  This is usually not
    necessary to interface with as it's used internally in the dispatching
    to click.  In future versions of Flask this object will most likely play
    a bigger role.  Typically it's created automatically by the
    :class:`FlaskGroup` but you can also manually create it and pass it
    onwards as click object.
    """

    def __init__(self, app_import_path=None, create_app=None):
        #: Optionally the import path for the Flask application.
        self.app_import_path = app_import_path or os.environ.get('FLASK_APP')
        #: Optionally a function that is passed the script info to create
        #: the instance of the application.
        self.create_app = create_app
        #: A dictionary with arbitrary data that can be associated with
        #: this script info.
        self.data = {}
        self._loaded_app = None

    def load_app(self):
        """Loads the Flask app (if not yet loaded) and returns it.  Calling
        this multiple times will just result in the already loaded app to
        be returned.
        """
        __traceback_hide__ = True

        if self._loaded_app is not None:
            return self._loaded_app

        app = None

        if self.create_app is not None:
            app = call_factory(self.create_app, self)
        else:
            if self.app_import_path:
                path, name = (self.app_import_path.split(':', 1) + [None])[:2]
                import_name = prepare_import(path)
                app = locate_app(self, import_name, name)
            else:
                for path in ('wsgi.py', 'app.py'):
                    import_name = prepare_import(path)
                    app = locate_app(
                        self, import_name, None, raise_if_not_found=False
                    )

                    if app:
                        break

        if not app:
            raise NoAppException(
                'Could not locate a Flask application. You did not provide '
                'the "FLASK_APP" environment variable, and a "wsgi.py" or '
                '"app.py" module was not found in the current directory.'
            )

        debug = get_debug_flag()

        if debug is not None:
            app._reconfigure_for_run_debug(debug)

        self._loaded_app = app
        return app


pass_script_info = click.make_pass_decorator(ScriptInfo, ensure=True)


def with_appcontext(f):
    """Wraps a callback so that it's guaranteed to be executed with the
    script's application context.  If callbacks are registered directly
    to the ``app.cli`` object then they are wrapped with this function
    by default unless it's disabled.
    """
    @click.pass_context
    def decorator(__ctx, *args, **kwargs):
        with __ctx.ensure_object(ScriptInfo).load_app().app_context():
            return __ctx.invoke(f, *args, **kwargs)
    return update_wrapper(decorator, f)


class AppGroup(click.Group):
    """This works similar to a regular click :class:`~click.Group` but it
    changes the behavior of the :meth:`command` decorator so that it
    automatically wraps the functions in :func:`with_appcontext`.

    Not to be confused with :class:`FlaskGroup`.
    """

    def command(self, *args, **kwargs):
        """This works exactly like the method of the same name on a regular
        :class:`click.Group` but it wraps callbacks in :func:`with_appcontext`
        unless it's disabled by passing ``with_appcontext=False``.
        """
        wrap_for_ctx = kwargs.pop('with_appcontext', True)
        def decorator(f):
            if wrap_for_ctx:
                f = with_appcontext(f)
            return click.Group.command(self, *args, **kwargs)(f)
        return decorator

    def group(self, *args, **kwargs):
        """This works exactly like the method of the same name on a regular
        :class:`click.Group` but it defaults the group class to
        :class:`AppGroup`.
        """
        kwargs.setdefault('cls', AppGroup)
        return click.Group.group(self, *args, **kwargs)


class FlaskGroup(AppGroup):
    """Special subclass of the :class:`AppGroup` group that supports
    loading more commands from the configured Flask app.  Normally a
    developer does not have to interface with this class but there are
    some very advanced use cases for which it makes sense to create an
    instance of this.

    For information as of why this is useful see :ref:`custom-scripts`.

    :param add_default_commands: if this is True then the default run and
        shell commands wil be added.
    :param add_version_option: adds the ``--version`` option.
    :param create_app: an optional callback that is passed the script info and
        returns the loaded app.
    :param load_dotenv: Load the nearest :file:`.env` and :file:`.flaskenv`
        files to set environment variables. Will also change the working
        directory to the directory containing the first file found.

    .. versionchanged:: 1.0
        If installed, python-dotenv will be used to load environment variables
        from :file:`.env` and :file:`.flaskenv` files.
    """

    def __init__(
        self, add_default_commands=True, create_app=None,
        add_version_option=True, load_dotenv=True, **extra
    ):
        params = list(extra.pop('params', None) or ())

        if add_version_option:
            params.append(version_option)

        AppGroup.__init__(self, params=params, **extra)
        self.create_app = create_app
        self.load_dotenv = load_dotenv

        if add_default_commands:
            self.add_command(run_command)
            self.add_command(shell_command)
            self.add_command(routes_command)

        self._loaded_plugin_commands = False

    def _load_plugin_commands(self):
        if self._loaded_plugin_commands:
            return
        try:
            import pkg_resources
        except ImportError:
            self._loaded_plugin_commands = True
            return

        for ep in pkg_resources.iter_entry_points('flask.commands'):
            self.add_command(ep.load(), ep.name)
        self._loaded_plugin_commands = True

    def get_command(self, ctx, name):
        self._load_plugin_commands()

        # We load built-in commands first as these should always be the
        # same no matter what the app does.  If the app does want to
        # override this it needs to make a custom instance of this group
        # and not attach the default commands.
        #
        # This also means that the script stays functional in case the
        # application completely fails.
        rv = AppGroup.get_command(self, ctx, name)
        if rv is not None:
            return rv

        info = ctx.ensure_object(ScriptInfo)
        try:
            rv = info.load_app().cli.get_command(ctx, name)
            if rv is not None:
                return rv
        except NoAppException:
            pass

    def list_commands(self, ctx):
        self._load_plugin_commands()

        # The commands available is the list of both the application (if
        # available) plus the builtin commands.
        rv = set(click.Group.list_commands(self, ctx))
        info = ctx.ensure_object(ScriptInfo)
        try:
            rv.update(info.load_app().cli.list_commands(ctx))
        except Exception:
            # Here we intentionally swallow all exceptions as we don't
            # want the help page to break if the app does not exist.
            # If someone attempts to use the command we try to create
            # the app again and this will give us the error.
            # However, we will not do so silently because that would confuse
            # users.
            traceback.print_exc()
        return sorted(rv)

    def main(self, *args, **kwargs):
        # Set a global flag that indicates that we were invoked from the
        # command line interface. This is detected by Flask.run to make the
        # call into a no-op. This is necessary to avoid ugly errors when the
        # script that is loaded here also attempts to start a server.
        os.environ['FLASK_RUN_FROM_CLI'] = 'true'

        if self.load_dotenv:
            load_dotenv()

        obj = kwargs.get('obj')

        if obj is None:
            obj = ScriptInfo(create_app=self.create_app)

        kwargs['obj'] = obj
        kwargs.setdefault('auto_envvar_prefix', 'FLASK')
        return super(FlaskGroup, self).main(*args, **kwargs)


def _path_is_ancestor(path, other):
    """Take ``other`` and remove the length of ``path`` from it. Then join it
    to ``path``. If it is the original value, ``path`` is an ancestor of
    ``other``."""
    return os.path.join(path, other[len(path):].lstrip(os.sep)) == other


def load_dotenv(path=None):
    """Load "dotenv" files in order of precedence to set environment variables.

    If an env var is already set it is not overwritten, so earlier files in the
    list are preferred over later files.

    Changes the current working directory to the location of the first file
    found, with the assumption that it is in the top level project directory
    and will be where the Python path should import local packages from.

    This is a no-op if `python-dotenv`_ is not installed.

    .. _python-dotenv: https://github.com/theskumar/python-dotenv#readme

    :param path: Load the file at this location instead of searching.
    :return: ``True`` if a file was loaded.

    .. versionadded:: 1.0
    """

    if dotenv is None:
        return

    if path is not None:
        return dotenv.load_dotenv(path)

    new_dir = None

    for name in ('.env', '.flaskenv'):
        path = dotenv.find_dotenv(name, usecwd=True)

        if not path:
            continue

        if new_dir is None:
            new_dir = os.path.dirname(path)

        dotenv.load_dotenv(path)

    if new_dir and os.getcwd() != new_dir:
        os.chdir(new_dir)

    return new_dir is not None  # at least one file was located and loaded


@click.command('run', short_help='Runs a development server.')
@click.option('--host', '-h', default='127.0.0.1',
              help='The interface to bind to.')
@click.option('--port', '-p', default=5000,
              help='The port to bind to.')
@click.option('--reload/--no-reload', default=None,
              help='Enable or disable the reloader.  By default the reloader '
              'is active if debug is enabled.')
@click.option('--debugger/--no-debugger', default=None,
              help='Enable or disable the debugger.  By default the debugger '
              'is active if debug is enabled.')
@click.option('--eager-loading/--lazy-loader', default=None,
              help='Enable or disable eager loading.  By default eager '
              'loading is enabled if the reloader is disabled.')
@click.option('--with-threads/--without-threads', default=False,
              help='Enable or disable multithreading.')
@pass_script_info
def run_command(info, host, port, reload, debugger, eager_loading,
                with_threads):
    """Runs a local development server for the Flask application.

    This local server is recommended for development purposes only but it
    can also be used for simple intranet deployments.  By default it will
    not support any sort of concurrency at all to simplify debugging.  This
    can be changed with the --with-threads option which will enable basic
    multithreading.

    The reloader and debugger are by default enabled if the debug flag of
    Flask is enabled and disabled otherwise.
    """
    from werkzeug.serving import run_simple

    debug = get_debug_flag()
    if reload is None:
        reload = bool(debug)
    if debugger is None:
        debugger = bool(debug)
    if eager_loading is None:
        eager_loading = not reload

    app = DispatchingApp(info.load_app, use_eager_loading=eager_loading)

    # Extra startup messages.  This depends a bit on Werkzeug internals to
    # not double execute when the reloader kicks in.
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        # If we have an import path we can print it out now which can help
        # people understand what's being served.  If we do not have an
        # import path because the app was loaded through a callback then
        # we won't print anything.
        if info.app_import_path is not None:
            print(' * Serving Flask app "%s"' % info.app_import_path)
        if debug is not None:
            print(' * Forcing debug mode %s' % (debug and 'on' or 'off'))

    run_simple(host, port, app, use_reloader=reload,
               use_debugger=debugger, threaded=with_threads)


@click.command('shell', short_help='Runs a shell in the app context.')
@with_appcontext
def shell_command():
    """Runs an interactive Python shell in the context of a given
    Flask application.  The application will populate the default
    namespace of this shell according to it's configuration.

    This is useful for executing small snippets of management code
    without having to manually configuring the application.
    """
    import code
    from flask.globals import _app_ctx_stack
    app = _app_ctx_stack.top.app
    banner = 'Python %s on %s\nApp: %s%s\nInstance: %s' % (
        sys.version,
        sys.platform,
        app.import_name,
        app.debug and ' [debug]' or '',
        app.instance_path,
    )
    ctx = {}

    # Support the regular Python interpreter startup script if someone
    # is using it.
    startup = os.environ.get('PYTHONSTARTUP')
    if startup and os.path.isfile(startup):
        with open(startup, 'r') as f:
            eval(compile(f.read(), startup, 'exec'), ctx)

    ctx.update(app.make_shell_context())

    code.interact(banner=banner, local=ctx)


@click.command('routes', short_help='Show the routes for the app.')
@click.option(
    '--sort', '-s',
    type=click.Choice(('endpoint', 'methods', 'rule', 'match')),
    default='endpoint',
    help=(
        'Method to sort routes by. "match" is the order that Flask will match '
        'routes when dispatching a request.'
    )
)
@click.option(
    '--all-methods',
    is_flag=True,
    help="Show HEAD and OPTIONS methods."
)
@with_appcontext
def routes_command(sort, all_methods):
    """Show all registered routes with endpoints and methods."""

    rules = list(current_app.url_map.iter_rules())
    ignored_methods = set(() if all_methods else ('HEAD', 'OPTIONS'))

    if sort in ('endpoint', 'rule'):
        rules = sorted(rules, key=attrgetter(sort))
    elif sort == 'methods':
        rules = sorted(rules, key=lambda rule: sorted(rule.methods))

    rule_methods = [
        ', '.join(sorted(rule.methods - ignored_methods)) for rule in rules
    ]

    headers = ('Endpoint', 'Methods', 'Rule')
    widths = (
        max(len(rule.endpoint) for rule in rules),
        max(len(methods) for methods in rule_methods),
        max(len(rule.rule) for rule in rules),
    )
    widths = [max(len(h), w) for h, w in zip(headers, widths)]
    row = '{{0:<{0}}}  {{1:<{1}}}  {{2:<{2}}}'.format(*widths)

    click.echo(row.format(*headers).strip())
    click.echo(row.format(*('-' * width for width in widths)))

    for rule, methods in zip(rules, rule_methods):
        click.echo(row.format(rule.endpoint, methods, rule.rule).rstrip())


cli = FlaskGroup(help="""\
This shell command acts as general utility script for Flask applications.

It loads the application configured (through the FLASK_APP environment
variable) and then provides commands either provided by the application or
Flask itself.

The most useful commands are the "run" and "shell" command.

Example usage:

\b
  %(prefix)s%(cmd)s FLASK_APP=hello.py
  %(prefix)s%(cmd)s FLASK_DEBUG=1
  %(prefix)sflask run
""" % {
    'cmd': os.name == 'posix' and 'export' or 'set',
    'prefix': os.name == 'posix' and '$ ' or '',
})


def main(as_module=False):
    args = sys.argv[1:]

    if as_module:
        this_module = 'flask'

        if sys.version_info < (2, 7):
            this_module += '.cli'

        name = 'python -m ' + this_module

        # Python rewrites "python -m flask" to the path to the file in argv.
        # Restore the original command so that the reloader works.
        sys.argv = ['-m', this_module] + args
    else:
        name = None

    cli.main(args=args, prog_name=name)


if __name__ == '__main__':
    main(as_module=True)
