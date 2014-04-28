# -*- coding: utf-8 -*-
"""
    flask.run
    ~~~~~~~~~

    A simple command line application to run flask apps.

    :copyright: (c) 2014 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import os
import sys
from threading import Lock
from contextlib import contextmanager

import click

from ._compat import iteritems


class NoAppException(click.UsageError):
    """Raised if an application cannot be found or loaded."""


def find_best_app(module):
    """Given a module instance this tries to find the best possible
    application in the module or raises an exception.
    """
    from . import Flask

    # Search for the most common names first.
    for attr_name in 'app', 'application':
        app = getattr(module, attr_name, None)
        if app is not None and isinstance(app, Flask):
            return app

    # Otherwise find the only object that is a Flask instance.
    matches = [v for k, v in iteritems(module.__dict__)
               if isinstance(v, Flask)]

    if matches:
        if len(matches) > 1:
            raise NoAppException('More than one possible Flask application '
                                 'found in module "%s", none of which are called '
                                 '"app".  Be explicit!' % module.__name__)
        return matches[0]

    raise NoAppException('Failed to find application in module "%s".  Are '
                         'you sure it contains a Flask application?  Maybe '
                         'you wrapped it in a WSGI middleware or you are '
                         'using a factory function.' % module.__name__)


def prepare_exec_for_file(filename):
    """Given a filename this will try to calculate the python path, add it
    to the search path and return the actual module name that is expected.
    """
    module = []

    # Chop off file extensions or package markers
    if filename.endswith('.py'):
        filename = filename[:-3]
    elif os.path.split(filename)[1] == '__init__.py':
        filename = os.path.dirname(filename)
    filename = os.path.realpath(filename)

    dirpath = filename
    while 1:
        dirpath, extra = os.path.split(dirpath)
        module.append(extra)
        if not os.path.isfile(os.path.join(dirpath, '__init__.py')):
            break

    sys.path.insert(0, dirpath)
    return '.'.join(module[::-1])


def locate_app(app_id, debug=None):
    """Attempts to locate the application."""
    if ':' in app_id:
        module, app_obj = app_id.split(':', 1)
    else:
        module = app_id
        app_obj = None

    __import__(module)
    mod = sys.modules[module]
    if app_obj is None:
        app = find_best_app(mod)
    else:
        app = getattr(mod, app_obj, None)
        if app is None:
            raise RuntimeError('Failed to find application in module "%s"'
                               % module)
    if debug is not None:
        app.debug = debug
    return app


class DispatchingApp(object):
    """Special application that dispatches to a flask application which
    is imported by name on first request.  This is safer than importing
    the application upfront because it means that we can forward all
    errors for import problems into the browser as error.
    """

    def __init__(self, app_id, debug=None, use_eager_loading=False):
        self.app_id = app_id
        self.app = None
        self.debug = debug
        self._lock = Lock()
        if use_eager_loading:
            self._load_unlocked()

    def _load_unlocked(self):
        self.app = rv = locate_app(self.app_id, self.debug)
        return rv

    def __call__(self, environ, start_response):
        if self.app is not None:
            return self.app(environ, start_response)
        with self._lock:
            if self.app is not None:
                rv = self.app
            else:
                rv = self._load_unlocked()
            return rv(environ, start_response)


class ScriptInfo(object):
    """Help object to deal with Flask applications.  This is usually not
    necessary to interface with as it's used internally in the dispatching
    to click.
    """

    def __init__(self):
        self.app_import_path = None
        self.debug = None
        self._loaded_app = None

    def get_app_import_path(self):
        """Return the actual application import path or fails if it is
        not yet set.
        """
        if self.app_import_path is not None:
            return self.app_import_path
        raise NoAppException('Could not locate application. '
                             'You did not provide FLASK_APP or the '
                             '--app parameter.')

    def load_app(self):
        """Loads the app (if not yet loaded) and returns it."""
        if self._loaded_app is not None:
            return self._loaded_app
        rv = locate_app(self.get_app_import_path(), self.debug)
        self._loaded_app = rv
        return rv

    @contextmanager
    def conditional_context(self, with_context=True):
        """Creates an application context or not, depending on the
        given parameter but always works as context manager.
        """
        if with_context:
            with self.load_app().app_context() as ctx:
                yield ctx
        else:
            yield None


pass_script_info = click.make_pass_decorator(ScriptInfo)


def without_appcontext(f):
    """Marks a click callback so that it does not get a app context
    created.  This only works for commands directly registered to
    the toplevel system.  This really is only useful for very
    special commands like the runserver one.
    """
    f.__flask_without_appcontext__ = True
    return f


class FlaskClickGroup(click.Group):
    """Special subclass of the a regular click group that supports
    loading more commands from the configured Flask app.
    """

    def __init__(self, help=None):
        def set_app_id(ctx, value):
            if value is not None:
                if os.path.isfile(value):
                    value = prepare_exec_for_file(value)
                elif '.' not in sys.path:
                    sys.path.insert(0, '.')
            ctx.obj.app_import_path = value
        def set_debug(ctx, value):
            ctx.obj.debug = value

        click.Group.__init__(self, help=help, params=[
            click.Option(['-a', '--app'],
                         help='The application to run',
                         callback=set_app_id, is_eager=True),
            click.Option(['--debug/--no-debug'],
                         help='Enable or disable debug mode.',
                         default=None, callback=set_debug)
        ])

    def get_command(self, ctx, name):
        info = ctx.find_object(ScriptInfo)
        # Find the command in the application first, if we can find it.
        # If the app is not available, we just ignore this silently.
        try:
            rv = info.load_app().cli.get_command(ctx, name)
            if rv is not None:
                return rv
        except NoAppException:
            pass
        return click.Group.get_command(self, ctx, name)

    def list_commands(self, ctx):
        # The commands available is the list of both the application (if
        # available) plus the builtin commands.
        rv = set(click.Group.list_commands(self, ctx))
        info = ctx.find_object(ScriptInfo)
        try:
            rv.update(info.load_app().cli.list_commands(ctx))
        except NoAppException:
            pass
        return sorted(rv)

    def invoke_subcommand(self, ctx, cmd, cmd_name, args):
        with_context = cmd.callback is None or \
           not getattr(cmd.callback, '__flask_without_appcontext__', False)

        with ctx.find_object(ScriptInfo).conditional_context(with_context):
            return click.Group.invoke_subcommand(
                self, ctx, cmd, cmd_name, args)


cli = FlaskClickGroup(help='''\
This shell command acts as general utility script for Flask applications.

It loads the application configured (either through the FLASK_APP environment
variable or the --app parameter) and then provides commands either provided
by the application or Flask itself.

The most useful commands are the "run" and "shell" command.

Example usage:

  flask --app=hello --debug run
''')


@cli.command('run', short_help='Runs a development server.')
@click.option('--host', '-h', default='127.0.0.1',
              help='The interface to bind to.')
@click.option('--port', '-p', default=5000,
              help='The port to bind to.')
@click.option('--reload/--no-reload', default=None,
              help='Enable or disable the reloader.  By default the reloader '
              'is active is debug is enabled.')
@click.option('--debugger/--no-debugger', default=None,
              help='Enable or disable the debugger.  By default the debugger '
              'is active if debug is enabled.')
@click.option('--eager-loading/--lazy-loader', default=None,
              help='Enable or disable eager loading.  By default eager '
              'loading is enabled if the reloader is disabled.')
@click.option('--with-threads/--without-threads', default=False,
              help='Enable or disable multithreading.')
@without_appcontext
@pass_script_info
def run_command(info, host, port, reload, debugger, eager_loading,
                with_threads):
    """Runs a local development server for the Flask application."""
    from werkzeug.serving import run_simple
    app_id = info.get_app_import_path()
    if reload is None:
        reload = info.debug
    if debugger is None:
        debugger = info.debug
    if eager_loading is None:
        eager_loading = not reload

    # Extra startup messages.  This depends a but on Werkzeug internals to
    # not double execute when the reloader kicks in.
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print(' * Serving Flask app "%s"' % app_id)
        if info.debug is not None:
            print(' * Forcing debug %s' % (info.debug and 'on' or 'off'))

    app = DispatchingApp(app_id, info.debug, eager_loading)
    run_simple(host, port, app, use_reloader=reload,
               use_debugger=debugger, threaded=with_threads)


@cli.command('shell', short_help='Runs a shell in the app context.')
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
    code.interact(banner=banner, local=app.make_shell_context())


def make_default_cli(app):
    """Creates the default click object for the app itself.  Currently
    there are no default commands registered because all builtin commands
    are registered on the actual cmd object here.
    """
    return click.Group()


def main(as_module=False):
    this_module = __package__ + '.cli'
    args = sys.argv[1:]

    if as_module:
        if sys.version_info >= (2, 7):
            name = 'python -m ' + this_module.rsplit('.', 1)[0]
        else:
            name = 'python -m ' + this_module

        # This module is always executed as "python -m flask.run" and as such
        # we need to ensure that we restore the actual command line so that
        # the reloader can properly operate.
        sys.argv = ['-m', this_module] + sys.argv[1:]
    else:
        name = 'flask'

    cli.main(args=args, prog_name=name, obj=ScriptInfo(),
             auto_envvar_prefix='FLASK')


if __name__ == '__main__':
    main(as_module=True)
