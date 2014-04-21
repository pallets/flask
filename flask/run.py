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
from optparse import OptionParser

from werkzeug.serving import run_simple

from ._compat import iteritems


def find_best_app(module):
    """Given a module instance this tries to find the best possible application
    in the module or raises a RuntimeError.
    """
    from flask import Flask

    # The app name wins, even if it's not a flask object.
    app = getattr(module, 'app', None)
    if app is not None and callable(app):
        return app

    # Otherwise find the first object named Flask
    matches = []
    for key, value in iteritems(module.__dict__):
        if isinstance(value, Flask):
            matches.append(value)

    if matches:
        if len(matches) > 1:
            raise RuntimeError('More than one possible Flask application '
                               'found in module "%s", none of which are called '
                               '"app".  Be explicit!' % module)
        return matches[0]

    raise RuntimeError('Failed to find application in module "%s".  Are '
                       'you sure it contains a Flask application?  Maybe '
                       'you wrapped it in a WSGI middleware or you are '
                       'using a factory function.' % module)


def prepare_exec_for_file(filename):
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
    """Special applicationt that dispatches to a flask application which
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


def run_application(app_id, host='127.0.0.1', port=5000, debug=None,
                    use_reloader=False, use_debugger=False,
                    use_eager_loading=None, magic_app_id=True,
                    **options):
    """Useful function to start a Werkzeug server for an application that
    is known by it's import name.  By default the app ID can also be a
    full file name in which case Flask attempts to reconstruct the import
    name from it and do the right thing.

    :param app_id: the import name of the application module.  If a colon
                   is provided, everything afterwards is the application
                   object name.  In case the magic app id is enabled this
                   can also be a filename.
    :param host: the host to bind to.
    :param port: the port to bind to.
    :param debug: if set to something other than None then the application's
                  debug flag will be set to this.
    :param use_reloader: enables or disables the reloader.
    :param use_debugger: enables or disables the builtin debugger.
    :param use_eager_loading: enables or disables eager loading.  This is
                              normally conditional to the reloader.
    :param magic_app_id: if this is enabled then the app id can also be a
                         filename instead of an import module and Flask
                         will attempt to reconstruct the import name.
    :param options: the options to be forwarded to the underlying
                    Werkzeug server.  See
                    :func:`werkzeug.serving.run_simple` for more
                    information.
    """
    if magic_app_id:
        if os.path.isfile(app_id) or os.sep in app_id or \
           os.altsep is not None and os.altsep in app_id:
            app_id = prepare_exec_for_file(app_id)

    if use_eager_loading is None:
        use_eager_loading = not use_reloader

    # Extra startup messages.  This depends a but on Werkzeug internals to
    # not double execute when the reloader kicks in.
    if os.environ.get('WERKZEUG_RUN_MAIN') != 'true':
        print ' * Serving Flask app "%s"' % app_id
        if debug is not None:
            print ' * Forcing debug %s' % (debug and 'on' or 'off')

    app = DispatchingApp(app_id, debug, use_eager_loading)
    run_simple(host, port, app, use_reloader=use_reloader,
               use_debugger=use_debugger, **options)


def main(as_module=False):
    this_module = __package__ + '.run'

    if as_module:
        if sys.version_info >= (2, 7):
            name = 'python -m ' + this_module.rsplit('.', 1)[0]
        else:
            name = 'python -m ' + this_module
    else:
        name = 'flask-run'

    parser = OptionParser(usage='%prog [options] module', prog=name)
    parser.add_option('--debug', action='store_true',
                      dest='debug', help='Flip debug flag on.  If enabled '
                      'this also affects debugger and reloader defaults.')
    parser.add_option('--no-debug', action='store_false',
                      dest='debug', help='Flip debug flag off.')
    parser.add_option('--host', default='127.0.0.1',
                      help='The host to bind on. (defaults to 127.0.0.1)')
    parser.add_option('--port', default=5000,
                      help='The port to bind on. (defaults to 5000)')
    parser.add_option('--with-reloader', action='store_true',
                      dest='with_reloader',
                      help='Enable the reloader.')
    parser.add_option('--without-reloader', action='store_false',
                      dest='with_reloader',
                      help='Disable the reloader.')
    parser.add_option('--with-debugger', action='store_true',
                      dest='with_debugger',
                      help='Enable the debugger.')
    parser.add_option('--without-debugger', action='store_false',
                      dest='with_debugger',
                      help='Disable the debugger.')
    parser.add_option('--with-eager-loading', action='store_true',
                      dest='with_eager_loading',
                      help='Force enable the eager-loading.  This makes the '
                      'application load immediately but makes development '
                      'flows harder.  It\'s not recommended to enable eager '
                      'loading when the reloader is enabled as it can lead '
                      'to unexpected crashes.')
    parser.add_option('--without-eager-loading', action='store_false',
                      dest='with_eager_loading',
                      help='Disable the eager-loading.')
    parser.add_option('--with-threads', action='store_true',
                      dest='with_threads',
                      help='Enable multi-threading to handle multiple '
                      'requests concurrently.')
    parser.add_option('--without-threads', action='store_false',
                      dest='with_threads',
                      help='Disables multi-threading. (default)')
    opts, args = parser.parse_args()
    if len(args) != 1:
        parser.error('Expected exactly one argument which is the import '
                     'name of the application.')

    if opts.with_debugger is None:
        opts.with_debugger = opts.debug
    if opts.with_reloader is None:
        opts.with_reloader = opts.debug

    # This module is always executed as "python -m flask.run" and as such
    # we need to ensure that we restore the actual command line so that
    # the reloader can properly operate.
    sys.argv = ['-m', this_module] + sys.argv[1:]

    run_application(args[0], opts.host, opts.port, debug=opts.debug,
                    use_reloader=opts.with_reloader,
                    use_debugger=opts.with_debugger,
                    use_eager_loading=opts.with_eager_loading,
                    threaded=opts.with_threads)


if __name__ == '__main__':
    main(as_module=True)
