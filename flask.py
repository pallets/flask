# -*- coding: utf-8 -*-
"""
    flask
    ~~~~~

    A microframework based on Werkzeug.  It's extensively documented
    and follows best practice patterns.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
import os
import sys
import pkg_resources
from threading import local
from jinja2 import Environment, PackageLoader
from werkzeug import Request, Response, LocalStack, LocalProxy
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, InternalServerError
from werkzeug.contrib.securecookie import SecureCookie

# try to import the json helpers
try:
    from simplejson import loads as load_json, dumps as dump_json
except ImportError:
    try:
        from json import loads as load_json, dumps as dump_json
    except ImportError:
        pass

# utilities we import from Werkzeug and Jinja2 that are unused
# in the module but are exported as public interface.
from werkzeug import abort, redirect, secure_filename, cached_property, \
     html, import_string, generate_password_hash, check_password_hash
from jinja2 import Markup, escape


class FlaskRequest(Request):
    """The request object used by default in flask.  Remembers the
    matched endpoint and view arguments.
    """

    def __init__(self, environ):
        Request.__init__(self, environ)
        self.endpoint = None
        self.view_args = None


class FlaskResponse(Response):
    """The response object that is used by default in flask.  Works like the
    response object from Werkzeug but is set to have a HTML mimetype by
    default.
    """
    default_mimetype = 'text/html'


class _RequestGlobals(object):
    pass


class _RequestContext(object):
    """The request context contains all request relevant information.  It is
    created at the beginning of the request and pushed to the
    `_request_ctx_stack` and removed at the end of it.  It will create the
    URL adapter and request object for the WSGI environment provided.
    """

    def __init__(self, app, environ):
        self.app = app
        self.url_adapter = app.url_map.bind_to_environ(environ)
        self.request = app.request_class(environ)
        self.session = app.open_session(self.request)
        self.g = _RequestGlobals()
        self.flashes = None


def url_for(endpoint, **values):
    """Generates a URL to the given endpoint with the method provided.

    :param endpoint: the endpoint of the URL (name of the function)
    :param values: the variable arguments of the URL rule
    """
    return _request_ctx_stack.top.url_adapter.build(endpoint, values)


def jsonified(**values):
    """Returns a json response"""
    return current_app.response_class(dump_json(values),
                                      mimetype='application/json')


def flash(message):
    """Flashes a message to the next request.  In order to remove the
    flashed message from the session and to display it to the user,
    the template has to call :func:`get_flashed_messages`.
    """
    session['_flashes'] = (session.get('_flashes', [])) + [message]


def get_flashed_messages():
    """Pulls all flashed messages from the session and returns them.
    Further calls in the same request to the function will return
    the same messages.
    """
    flashes = _request_ctx_stack.top.flashes
    if flashes is None:
        _request_ctx_stack.top.flashes = flashes = \
            session.pop('_flashes', [])
    return flashes


def render_template(template_name, **context):
    """Renders a template from the template folder with the given
    context.
    """
    return current_app.jinja_env.get_template(template_name).render(context)


def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context.
    """
    return current_app.jinja_env.from_string(source).render(context)


class Flask(object):
    """The flask object implements a WSGI application and acts as the central
    object.  It is passed the name of the module or package of the application
    and optionally a configuration.  When it's created it sets up the
    template engine and provides ways to register view functions.
    """

    #: the class that is used for request objects
    request_class = FlaskRequest

    #: the class that is used for response objects
    response_class = FlaskResponse

    #: path for the static files.  If you don't want to use static files
    #: you can set this value to `None` in which case no URL rule is added
    #: and the development server will no longer serve any static files.
    static_path = '/static'

    #: if a secret key is set, cryptographic components can use this to
    #: sign cookies and other things.  Set this to a complex random value
    #: when you want to use the secure cookie for instance.
    secret_key = None

    #: The secure cookie uses this for the name of the session cookie
    session_cookie_name = 'session'

    #: options that are passed directly to the Jinja2 environment
    jinja_options = dict(
        autoescape=True,
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_']
    )

    def __init__(self, package_name):
        self.debug = False
        self.package_name = package_name
        self.view_functions = {}
        self.error_handlers = {}
        self.request_init_funcs = []
        self.request_shutdown_funcs = []
        self.url_map = Map()

        if self.static_path is not None:
            self.url_map.add(Rule(self.static_path + '/<filename>',
                                  build_only=True, endpoint='static'))

        self.jinja_env = Environment(loader=self.create_jinja_loader(),
                                     **self.jinja_options)
        self.jinja_env.globals.update(
            url_for=url_for,
            request=request,
            session=session,
            g=g,
            get_flashed_messages=get_flashed_messages
        )

    def create_jinja_loader(self):
        """Creates the Jinja loader.  By default just a package loader for
        the configured package is returned that looks up templates in the
        `templates` folder.  To add other loaders it's possible to
        override this method.
        """
        return PackageLoader(self.package_name)

    def run(self, host='localhost', port=5000, **options):
        """Runs the application on a local development server"""
        from werkzeug import run_simple
        if 'debug' in options:
            self.debug = options.pop('debug')
        if self.static_path is not None:
            options['static_files'] = {
                self.static_path:   (self.package_name, 'static')
            }
        options.setdefault('use_reloader', self.debug)
        options.setdefault('use_debugger', self.debug)
        return run_simple(host, port, self, **options)

    @cached_property
    def test(self):
        """A test client for this application"""
        from werkzeug import Client
        return Client(self, self.response_class, use_cookies=True)

    def open_resource(self, resource):
        """Opens a resource from the application's resource folder"""
        return pkg_resources.resource_stream(self.package_name, resource)

    def open_session(self, request):
        """Creates or opens a new session.  Default implementation requires
        that `securecookie.secret_key` is set.
        """
        key = self.secret_key
        if key is not None:
            return SecureCookie.load_cookie(request, self.session_cookie_name,
                                            secret_key=key)

    def save_session(self, session, response):
        """Saves the session if it needs updates."""
        if session is not None:
            session.save_cookie(response, self.session_cookie_name)

    def route(self, rule, **options):
        """A decorator that is used to register a view function for a
        given URL rule.  Example::

            @app.route('/')
            def index():
                return 'Hello World'
        """
        def decorator(f):
            if 'endpoint' not in options:
                options['endpoint'] = f.__name__
            self.url_map.add(Rule(rule, **options))
            self.view_functions[options['endpoint']] = f
            return f
        return decorator

    def errorhandler(self, code):
        """A decorator that is used to register a function give a given
        error code.  Example::

            @app.errorhandler(404)
            def page_not_found():
                return 'This page does not exist', 404
        """
        def decorator(f):
            self.error_handlers[code] = f
            return f
        return decorator

    def request_init(self, f):
        """Registers a function to run before each request."""
        self.request_init_funcs.append(f)
        return f

    def request_shutdown(self, f):
        """Register a function to be run after each request."""
        self.request_shutdown_funcs.append(f)
        return f

    def match_request(self):
        """Matches the current request against the URL map and also
        stores the endpoint and view arguments on the request object
        is successful, otherwise the exception is stored.
        """
        rv = _request_ctx_stack.top.url_adapter.match()
        request.endpoint, request.view_args = rv
        return rv

    def dispatch_request(self):
        """Does the request dispatching.  Matches the URL and returns the
        return value of the view or error handler.  This does not have to
        be a response object.  In order to convert the return value to a
        proper response object, call :func:`make_response`.
        """
        try:
            endpoint, values = self.match_request()
            return self.view_functions[endpoint](**values)
        except HTTPException, e:
            handler = self.error_handlers.get(e.code)
            if handler is None:
                return e
            return handler(e)
        except Exception, e:
            handler = self.error_handlers.get(500)
            if self.debug or handler is None:
                raise
            return handler(e)

    def make_response(self, rv):
        """Converts the return value from a view function to a real
        response object that is an instance of :attr:`response_class`.
        """
        if isinstance(rv, self.response_class):
            return rv
        if isinstance(rv, basestring):
            return self.response_class(rv)
        if isinstance(rv, tuple):
            return self.response_class(*rv)
        return self.response_class.force_type(rv, request.environ)

    def preprocess_request(self):
        """Called before the actual request dispatching and will
        call every as :func:`request_init` decorated function.
        If any of these function returns a value it's handled as
        if it was the return value from the view and further
        request handling is stopped.
        """
        for func in self.request_init_funcs:
            rv = func()
            if rv is not None:
                return rv

    def process_response(self, response):
        """Can be overridden in order to modify the response object
        before it's sent to the WSGI server.
        """
        session = _request_ctx_stack.top.session
        if session is not None:
            self.save_session(session, response)
        for handler in self.request_shutdown_funcs:
            response = handler(response)
        return response

    def wsgi_app(self, environ, start_response):
        """The actual WSGI application.  This is not implemented in
        `__call__` so that middlewares can be applied:

            app.wsgi_app = MyMiddleware(app.wsgi_app)
        """
        _request_ctx_stack.push(_RequestContext(self, environ))
        try:
            rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request()
            response = self.make_response(rv)
            response = self.process_response(response)
            return response(environ, start_response)
        finally:
            _request_ctx_stack.pop()

    def __call__(self, environ, start_response):
        """Shortcut for :attr:`wsgi_app`"""
        return self.wsgi_app(environ, start_response)


# context locals
_request_ctx_stack = LocalStack()
current_app = LocalProxy(lambda: _request_ctx_stack.top.app)
request = LocalProxy(lambda: _request_ctx_stack.top.request)
session = LocalProxy(lambda: _request_ctx_stack.top.session)
g = LocalProxy(lambda: _request_ctx_stack.top.g)
