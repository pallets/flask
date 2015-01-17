# -*- coding: utf-8 -*-
"""
    werkzeug.debug
    ~~~~~~~~~~~~~~

    WSGI application traceback debugger.

    :copyright: (c) 2014 by the Werkzeug Team, see AUTHORS for more details.
    :license: BSD, see LICENSE for more details.
"""
import json
import mimetypes
from os.path import join, dirname, basename, isfile
from werkzeug.wrappers import BaseRequest as Request, BaseResponse as Response
from werkzeug.debug.tbtools import get_current_traceback, render_console_html
from werkzeug.debug.console import Console
from werkzeug.security import gen_salt


#: import this here because it once was documented as being available
#: from this module.  In case there are users left ...
from werkzeug.debug.repr import debug_repr


class _ConsoleFrame(object):
    """Helper class so that we can reuse the frame console code for the
    standalone console.
    """

    def __init__(self, namespace):
        self.console = Console(namespace)
        self.id = 0


class DebuggedApplication(object):
    """Enables debugging support for a given application::

        from werkzeug.debug import DebuggedApplication
        from myapp import app
        app = DebuggedApplication(app, evalex=True)

    The `evalex` keyword argument allows evaluating expressions in a
    traceback's frame context.

    .. versionadded:: 0.9
       The `lodgeit_url` parameter was deprecated.

    :param app: the WSGI application to run debugged.
    :param evalex: enable exception evaluation feature (interactive
                   debugging).  This requires a non-forking server.
    :param request_key: The key that points to the request object in ths
                        environment.  This parameter is ignored in current
                        versions.
    :param console_path: the URL for a general purpose console.
    :param console_init_func: the function that is executed before starting
                              the general purpose console.  The return value
                              is used as initial namespace.
    :param show_hidden_frames: by default hidden traceback frames are skipped.
                               You can show them by setting this parameter
                               to `True`.
    """

    # this class is public
    __module__ = 'werkzeug'

    def __init__(self, app, evalex=False, request_key='werkzeug.request',
                 console_path='/console', console_init_func=None,
                 show_hidden_frames=False, lodgeit_url=None):
        if lodgeit_url is not None:
            from warnings import warn
            warn(DeprecationWarning('Werkzeug now pastes into gists.'))
        if not console_init_func:
            console_init_func = dict
        self.app = app
        self.evalex = evalex
        self.frames = {}
        self.tracebacks = {}
        self.request_key = request_key
        self.console_path = console_path
        self.console_init_func = console_init_func
        self.show_hidden_frames = show_hidden_frames
        self.secret = gen_salt(20)

    def debug_application(self, environ, start_response):
        """Run the application and conserve the traceback frames."""
        app_iter = None
        try:
            app_iter = self.app(environ, start_response)
            for item in app_iter:
                yield item
            if hasattr(app_iter, 'close'):
                app_iter.close()
        except Exception:
            if hasattr(app_iter, 'close'):
                app_iter.close()
            traceback = get_current_traceback(skip=1, show_hidden_frames=
                                              self.show_hidden_frames,
                                              ignore_system_exceptions=True)
            for frame in traceback.frames:
                self.frames[frame.id] = frame
            self.tracebacks[traceback.id] = traceback

            try:
                start_response('500 INTERNAL SERVER ERROR', [
                    ('Content-Type', 'text/html; charset=utf-8'),
                    # Disable Chrome's XSS protection, the debug
                    # output can cause false-positives.
                    ('X-XSS-Protection', '0'),
                ])
            except Exception:
                # if we end up here there has been output but an error
                # occurred.  in that situation we can do nothing fancy any
                # more, better log something into the error log and fall
                # back gracefully.
                environ['wsgi.errors'].write(
                    'Debugging middleware caught exception in streamed '
                    'response at a point where response headers were already '
                    'sent.\n')
            else:
                yield traceback.render_full(evalex=self.evalex,
                                            secret=self.secret) \
                               .encode('utf-8', 'replace')

            traceback.log(environ['wsgi.errors'])

    def execute_command(self, request, command, frame):
        """Execute a command in a console."""
        return Response(frame.console.eval(command), mimetype='text/html')

    def display_console(self, request):
        """Display a standalone shell."""
        if 0 not in self.frames:
            self.frames[0] = _ConsoleFrame(self.console_init_func())
        return Response(render_console_html(secret=self.secret),
                        mimetype='text/html')

    def paste_traceback(self, request, traceback):
        """Paste the traceback and return a JSON response."""
        rv = traceback.paste()
        return Response(json.dumps(rv), mimetype='application/json')

    def get_source(self, request, frame):
        """Render the source viewer."""
        return Response(frame.render_source(), mimetype='text/html')

    def get_resource(self, request, filename):
        """Return a static resource from the shared folder."""
        filename = join(dirname(__file__), 'shared', basename(filename))
        if isfile(filename):
            mimetype = mimetypes.guess_type(filename)[0] \
                or 'application/octet-stream'
            f = open(filename, 'rb')
            try:
                return Response(f.read(), mimetype=mimetype)
            finally:
                f.close()
        return Response('Not Found', status=404)

    def __call__(self, environ, start_response):
        """Dispatch the requests."""
        # important: don't ever access a function here that reads the incoming
        # form data!  Otherwise the application won't have access to that data
        # any more!
        request = Request(environ)
        response = self.debug_application
        if request.args.get('__debugger__') == 'yes':
            cmd = request.args.get('cmd')
            arg = request.args.get('f')
            secret = request.args.get('s')
            traceback = self.tracebacks.get(request.args.get('tb', type=int))
            frame = self.frames.get(request.args.get('frm', type=int))
            if cmd == 'resource' and arg:
                response = self.get_resource(request, arg)
            elif cmd == 'paste' and traceback is not None and \
                 secret == self.secret:
                response = self.paste_traceback(request, traceback)
            elif cmd == 'source' and frame and self.secret == secret:
                response = self.get_source(request, frame)
            elif self.evalex and cmd is not None and frame is not None and \
                 self.secret == secret:
                response = self.execute_command(request, cmd, frame)
        elif self.evalex and self.console_path is not None and \
           request.path == self.console_path:
            response = self.display_console(request)
        return response(environ, start_response)
