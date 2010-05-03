# -*- coding: utf-8 -*-
"""
    flask
    ~~~~~

    A microframework based on Werkzeug.  It's extensively documented
    and follows best practice patterns.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from __future__ import with_statement
import os
import sys
from datetime import datetime, timedelta

from itertools import chain
from jinja2 import Environment, PackageLoader, FileSystemLoader
from werkzeug import Request as RequestBase, Response as ResponseBase, \
     LocalStack, LocalProxy, create_environ, SharedDataMiddleware, \
     ImmutableDict, cached_property
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException
from werkzeug.contrib.securecookie import SecureCookie

# try to load the best simplejson implementation available.  If JSON
# is not installed, we add a failing class.
json_available = True
try:
    import simplejson as json
except ImportError:
    try:
        import json
    except ImportError:
        json_available = False

# utilities we import from Werkzeug and Jinja2 that are unused
# in the module but are exported as public interface.
from werkzeug import abort, redirect
from jinja2 import Markup, escape

# use pkg_resource if that works, otherwise fall back to cwd.  The
# current working directory is generally not reliable with the notable
# exception of google appengine.
try:
    import pkg_resources
    pkg_resources.resource_stream
except (ImportError, AttributeError):
    pkg_resources = None


class Request(RequestBase):
    """The request object used by default in flask.  Remembers the
    matched endpoint and view arguments.

    It is what ends up as :class:`~flask.request`.  If you want to replace
    the request object used you can subclass this and set
    :attr:`~flask.Flask.request_class` to your subclass.
    """

    endpoint = view_args = routing_exception = None

    @property
    def module(self):
        """The name of the current module"""
        if self.endpoint and '.' in self.endpoint:
            return self.endpoint.rsplit('.', 1)[0]

    @cached_property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.
        """
        if __debug__:
            _assert_have_json()
        if self.mimetype == 'application/json':
            return json.loads(self.data)


class Response(ResponseBase):
    """The response object that is used by default in flask.  Works like the
    response object from Werkzeug but is set to have a HTML mimetype by
    default.  Quite often you don't have to create this object yourself because
    :meth:`~flask.Flask.make_response` will take care of that for you.

    If you want to replace the response object used you can subclass this and
    set :attr:`~flask.Flask.request_class` to your subclass.
    """
    default_mimetype = 'text/html'


class _RequestGlobals(object):
    pass


class Session(SecureCookie):
    """Expands the session for support for switching between permanent
    and non-permanent sessions.
    """

    def _get_permanent(self):
        return self.get('_permanent', False)
    def _set_permanent(self, value):
        self['_permanent'] = bool(value)
    permanent = property(_get_permanent, _set_permanent)
    del _get_permanent, _set_permanent


class _NullSession(Session):
    """Class used to generate nicer error messages if sessions are not
    available.  Will still allow read-only access to the empty session
    but fail on setting.
    """

    def _fail(self, *args, **kwargs):
        raise RuntimeError('the session is unavailable because no secret '
                           'key was set.  Set the secret_key on the '
                           'application to something unique and secret')
    __setitem__ = __delitem__ = clear = pop = popitem = \
        update = setdefault = _fail
    del _fail


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
        if self.session is None:
            self.session = _NullSession()
        self.g = _RequestGlobals()
        self.flashes = None

        try:
            self.request.endpoint, self.request.view_args = \
                self.url_adapter.match()
        except HTTPException, e:
            self.request.routing_exception = e

    def __enter__(self):
        _request_ctx_stack.push(self)

    def __exit__(self, exc_type, exc_value, tb):
        # do not pop the request stack if we are in debug mode and an
        # exception happened.  This will allow the debugger to still
        # access the request object in the interactive shell.
        if tb is None or not self.app.debug:
            _request_ctx_stack.pop()


def url_for(endpoint, **values):
    """Generates a URL to the given endpoint with the method provided.
    The endpoint is relative to the active module if modules are in use.

    Here some examples:

    ==================== ======================= =============================
    Active Module        Target Endpoint         Target Function
    ==================== ======================= =============================
    `None`               ``'index'``             `index` of the application
    `None`               ``'.index'``            `index` of the application
    ``'admin'``          ``'index'``             `index` of the `admin` module
    any                  ``'.index'``            `index` of the application
    any                  ``'admin.index'``       `index` of the `admin` module
    ==================== ======================= =============================

    Variable arguments that are unknown to the target endpoint are appended
    to the generated URL as query arguments.

    For more information, head over to the :ref:`Quickstart <url-building>`.

    :param endpoint: the endpoint of the URL (name of the function)
    :param values: the variable arguments of the URL rule
    :param _external: if set to `True`, an absolute URL is generated.
    """
    ctx = _request_ctx_stack.top
    if '.' not in endpoint:
        mod = ctx.request.module
        if mod is not None:
            endpoint = mod + '.' + endpoint
    elif endpoint.startswith('.'):
        endpoint = endpoint[1:]
    external = values.pop('_external', False)
    return ctx.url_adapter.build(endpoint, values, force_external=external)


def get_template_attribute(template_name, attribute):
    """Loads a macro (or variable) a template exports.  This can be used to
    invoke a macro from within Python code.  If you for example have a
    template named `_foo.html` with the following contents:

    .. sourcecode:: html+jinja

       {% macro hello(name) %}Hello {{ name }}!{% endmacro %}

    You can access this from Python code like this::

        hello = get_template_attribute('_foo.html', 'hello')
        return hello('World')

    .. versionadded:: 0.2

    :param template_name: the name of the template
    :param attribute: the name of the variable of macro to acccess
    """
    return getattr(current_app.jinja_env.get_template(template_name).module,
                   attribute)


def flash(message):
    """Flashes a message to the next request.  In order to remove the
    flashed message from the session and to display it to the user,
    the template has to call :func:`get_flashed_messages`.

    :param message: the message to be flashed.
    """
    session.setdefault('_flashes', []).append(message)


def get_flashed_messages():
    """Pulls all flashed messages from the session and returns them.
    Further calls in the same request to the function will return
    the same messages.
    """
    flashes = _request_ctx_stack.top.flashes
    if flashes is None:
        _request_ctx_stack.top.flashes = flashes = session.pop('_flashes', [])
    return flashes


def jsonify(*args, **kwargs):
    """Creates a :class:`~flask.Response` with the JSON representation of
    the given arguments with an `application/json` mimetype.  The arguments
    to this function are the same as to the :class:`dict` constructor.

    Example usage::

        @app.route('/_get_current_user')
        def get_current_user():
            return jsonify(username=g.user.username,
                           email=g.user.email,
                           id=g.user.id)

    This will send a JSON response like this to the browser::

        {
            "username": "admin",
            "email": "admin@localhost",
            "id": 42
        }

    This requires Python 2.6 or an installed version of simplejson.

    .. versionadded:: 0.2
    """
    if __debug__:
        _assert_have_json()
    return current_app.response_class(json.dumps(dict(*args, **kwargs),
        indent=None if request.is_xhr else 2), mimetype='application/json')


def render_template(template_name, **context):
    """Renders a template from the template folder with the given
    context.

    :param template_name: the name of the template to be rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    current_app.update_template_context(context)
    return current_app.jinja_env.get_template(template_name).render(context)


def render_template_string(source, **context):
    """Renders a template from the given template source string
    with the given context.

    :param template_name: the sourcecode of the template to be
                          rendered
    :param context: the variables that should be available in the
                    context of the template.
    """
    current_app.update_template_context(context)
    return current_app.jinja_env.from_string(source).render(context)


def _default_template_ctx_processor():
    """Default template context processor.  Injects `request`,
    `session` and `g`.
    """
    reqctx = _request_ctx_stack.top
    return dict(
        request=reqctx.request,
        session=reqctx.session,
        g=reqctx.g
    )


def _assert_have_json():
    """Helper function that fails if JSON is unavailable."""
    if not json_available:
        raise RuntimeError('simplejson not installed')


def _get_package_path(name):
    """Returns the path to a package or cwd if that cannot be found."""
    try:
        return os.path.abspath(os.path.dirname(sys.modules[name].__file__))
    except (KeyError, AttributeError):
        return os.getcwd()


# figure out if simplejson escapes slashes.  This behaviour was changed
# from one version to another without reason.
if not json_available or '\\/' not in json.dumps('/'):

    def _tojson_filter(*args, **kwargs):
        if __debug__:
            _assert_have_json()
        return json.dumps(*args, **kwargs).replace('/', '\\/')
else:
    _tojson_filter = json.dumps


class _PackageBoundObject(object):

    def __init__(self, import_name):
        #: the name of the package or module.  Do not change this once
        #: it was set by the constructor.
        self.import_name = import_name

        #: where is the app root located?
        self.root_path = _get_package_path(self.import_name)

    def open_resource(self, resource):
        """Opens a resource from the application's resource folder.  To see
        how this works, consider the following folder structure::

            /myapplication.py
            /schemal.sql
            /static
                /style.css
            /template
                /layout.html
                /index.html

        If you want to open the `schema.sql` file you would do the
        following::

            with app.open_resource('schema.sql') as f:
                contents = f.read()
                do_something_with(contents)

        :param resource: the name of the resource.  To access resources within
                         subfolders use forward slashes as separator.
        """
        if pkg_resources is None:
            return open(os.path.join(self.root_path, resource), 'rb')
        return pkg_resources.resource_stream(self.import_name, resource)


class _ModuleSetupState(object):

    def __init__(self, app, url_prefix=None):
        self.app = app
        self.url_prefix = url_prefix


class Module(_PackageBoundObject):
    """Container object that enables pluggable applications.  A module can
    be used to organize larger applications.  They represent blueprints that,
    in combination with a :class:`Flask` object are used to create a large
    application.

    A module is like an application bound to an `import_name`.  Multiple
    modules can share the same import names, but in that case a `name` has
    to be provided to keep them apart.  If different import names are used,
    the rightmost part of the import name is used as name.

    Here an example structure for a larger appliation::

        /myapplication
            /__init__.py
            /views
                /__init__.py
                /admin.py
                /frontend.py

    The `myapplication/__init__.py` can look like this::

        from flask import Flask
        from myapplication.views.admin import admin
        from myapplication.views.frontend import frontend

        app = Flask(__name__)
        app.register_module(admin, url_prefix='/admin')
        app.register_module(frontend)

    And here an example view module (`myapplication/views/admin.py`)::

        from flask import Module

        admin = Module(__name__)

        @admin.route('/')
        def index():
            pass

        @admin.route('/login')
        def login():
            pass

    For a gentle introduction into modules, checkout the
    :ref:`working-with-modules` section.
    """

    def __init__(self, import_name, name=None, url_prefix=None):
        if name is None:
            assert '.' in import_name, 'name required if package name ' \
                'does not point to a submodule'
            name = import_name.rsplit('.', 1)[1]
        _PackageBoundObject.__init__(self, import_name)
        self.name = name
        self.url_prefix = url_prefix
        self._register_events = []

    def route(self, rule, **options):
        """Like :meth:`Flask.route` but for a module.  The endpoint for the
        :func:`url_for` function is prefixed with the name of the module.
        """
        def decorator(f):
            self.add_url_rule(rule, f.__name__, f, **options)
            return f
        return decorator

    def add_url_rule(self, rule, endpoint, view_func=None, **options):
        """Like :meth:`Flask.add_url_rule` but for a module.  The endpoint for
        the :func:`url_for` function is prefixed with the name of the module.
        """
        def register_rule(state):
            the_rule = rule
            if self.url_prefix:
                the_rule = state.url_prefix + rule
            state.app.add_url_rule(the_rule, '%s.%s' % (self.name, endpoint),
                                   view_func, **options)
        self._record(register_rule)

    def before_request(self, f):
        """Like :meth:`Flask.before_request` but for a module.  This function
        is only executed before each request that is handled by a function of
        that module.
        """
        self._record(lambda s: s.app.before_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def before_app_request(self, f):
        """Like :meth:`Flask.before_request`.  Such a function is executed
        before each request.
        """
        self._record(lambda s: s.app.before_request_funcs
            .setdefault(None, []).append(f))
        return f

    def after_request(self, f):
        """Like :meth:`Flask.after_request` but for a module.  This function
        is only executed after each request that is handled by a function of
        that module.
        """
        self._record(lambda s: s.app.after_request_funcs
            .setdefault(self.name, []).append(f))
        return f

    def after_app_request(self, f):
        """Like :meth:`Flask.after_request` but for a module.  Such a function
        is executed after each request.
        """
        self._record(lambda s: s.app.after_request_funcs
            .setdefault(None, []).append(f))
        return f

    def _record(self, func):
        self._register_events.append(func)


class Flask(_PackageBoundObject):
    """The flask object implements a WSGI application and acts as the central
    object.  It is passed the name of the module or package of the
    application.  Once it is created it will act as a central registry for
    the view functions, the URL rules, template configuration and much more.

    The name of the package is used to resolve resources from inside the
    package or the folder the module is contained in depending on if the
    package parameter resolves to an actual python package (a folder with
    an `__init__.py` file inside) or a standard module (just a `.py` file).

    For more information about resource loading, see :func:`open_resource`.

    Usually you create a :class:`Flask` instance in your main module or
    in the `__init__.py` file of your package like this::

        from flask import Flask
        app = Flask(__name__)
    """

    #: the class that is used for request objects.  See :class:`~flask.request`
    #: for more information.
    request_class = Request

    #: the class that is used for response objects.  See
    #: :class:`~flask.Response` for more information.
    response_class = Response

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

    #: A :class:`~datetime.timedelta` which is used to set the expiration
    #: date of a permanent session.  The default is 31 days which makes a
    #: permanent session survive for roughly one month.
    permanent_session_lifetime = timedelta(days=31)

    #: options that are passed directly to the Jinja2 environment
    jinja_options = ImmutableDict(
        autoescape=True,
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_']
    )

    def __init__(self, import_name):
        _PackageBoundObject.__init__(self, import_name)

        #: the debug flag.  Set this to `True` to enable debugging of
        #: the application.  In debug mode the debugger will kick in
        #: when an unhandled exception ocurrs and the integrated server
        #: will automatically reload the application if changes in the
        #: code are detected.
        self.debug = False

        #: a dictionary of all view functions registered.  The keys will
        #: be function names which are also used to generate URLs and
        #: the values are the function objects themselves.
        #: to register a view function, use the :meth:`route` decorator.
        self.view_functions = {}

        #: a dictionary of all registered error handlers.  The key is
        #: be the error code as integer, the value the function that
        #: should handle that error.
        #: To register a error handler, use the :meth:`errorhandler`
        #: decorator.
        self.error_handlers = {}

        #: a dictionary with lists of functions that should be called at the
        #: beginning of the request.  The key of the dictionary is the name of
        #: the module this function is active for, `None` for all requests.
        #: This can for example be used to open database connections or
        #: getting hold of the currently logged in user.  To register a
        #: function here, use the :meth:`before_request` decorator.
        self.before_request_funcs = {}

        #: a dictionary with lists of functions that should be called after
        #: each request.  The key of the dictionary is the name of the module
        #: this function is active for, `None` for all requests.  This can for
        #: example be used to open database connections or getting hold of the
        #: currently logged in user.  To register a function here, use the
        #: :meth:`before_request` decorator.
        self.after_request_funcs = {}

        #: a dictionary with list of functions that are called without arguments
        #: to populate the template context.  They key of the dictionary is the
        #: name of the module this function is active for, `None` for all
        #: requests.  Each returns a dictionary that the template context is
        #: updated with.  To register a function here, use the
        #: :meth:`context_processor` decorator.
        self.template_context_processors = {
            None: [_default_template_ctx_processor]
        }

        #: the :class:`~werkzeug.routing.Map` for this instance.  You can use
        #: this to change the routing converters after the class was created
        #: but before any routes are connected.  Example::
        #:
        #:    from werkzeug import BaseConverter
        #:
        #:    class ListConverter(BaseConverter):
        #:        def to_python(self, value):
        #:            return value.split(',')
        #:        def to_url(self, values):
        #:            return ','.join(BaseConverter.to_url(value)
        #:                            for value in values)
        #:
        #:    app = Flask(__name__)
        #:    app.url_map.converters['list'] = ListConverter
        self.url_map = Map()

        if self.static_path is not None:
            self.add_url_rule(self.static_path + '/<filename>',
                              build_only=True, endpoint='static')
            if pkg_resources is not None:
                target = (self.import_name, 'static')
            else:
                target = os.path.join(self.root_path, 'static')
            self.wsgi_app = SharedDataMiddleware(self.wsgi_app, {
                self.static_path: target
            })

        #: the Jinja2 environment.  It is created from the
        #: :attr:`jinja_options` and the loader that is returned
        #: by the :meth:`create_jinja_loader` function.
        self.jinja_env = Environment(loader=self.create_jinja_loader(),
                                     **self.jinja_options)
        self.jinja_env.globals.update(
            url_for=url_for,
            get_flashed_messages=get_flashed_messages
        )
        self.jinja_env.filters['tojson'] = _tojson_filter

    def create_jinja_loader(self):
        """Creates the Jinja loader.  By default just a package loader for
        the configured package is returned that looks up templates in the
        `templates` folder.  To add other loaders it's possible to
        override this method.
        """
        if pkg_resources is None:
            return FileSystemLoader(os.path.join(self.root_path, 'templates'))
        return PackageLoader(self.import_name)

    def update_template_context(self, context):
        """Update the template context with some commonly used variables.
        This injects request, session and g into the template context.

        :param context: the context as a dictionary that is updated in place
                        to add extra variables.
        """
        funcs = self.template_context_processors[None]
        mod = _request_ctx_stack.top.request.module
        if mod is not None and mod in self.template_context_processors:
            funcs = chain(funcs, self.template_context_processors[mod])
        for func in funcs:
            context.update(func())

    def run(self, host='127.0.0.1', port=5000, **options):
        """Runs the application on a local development server.  If the
        :attr:`debug` flag is set the server will automatically reload
        for code changes and show a debugger in case an exception happened.

        :param host: the hostname to listen on.  set this to ``'0.0.0.0'``
                     to have the server available externally as well.
        :param port: the port of the webserver
        :param options: the options to be forwarded to the underlying
                        Werkzeug server.  See :func:`werkzeug.run_simple`
                        for more information.
        """
        from werkzeug import run_simple
        if 'debug' in options:
            self.debug = options.pop('debug')
        options.setdefault('use_reloader', self.debug)
        options.setdefault('use_debugger', self.debug)
        return run_simple(host, port, self, **options)

    def test_client(self):
        """Creates a test client for this application.  For information
        about unit testing head over to :ref:`testing`.
        """
        from werkzeug import Client
        return Client(self, self.response_class, use_cookies=True)

    def open_session(self, request):
        """Creates or opens a new session.  Default implementation stores all
        session data in a signed cookie.  This requires that the
        :attr:`secret_key` is set.

        :param request: an instance of :attr:`request_class`.
        """
        key = self.secret_key
        if key is not None:
            return Session.load_cookie(request, self.session_cookie_name,
                                       secret_key=key)

    def save_session(self, session, response):
        """Saves the session if it needs updates.  For the default
        implementation, check :meth:`open_session`.

        :param session: the session to be saved (a
                        :class:`~werkzeug.contrib.securecookie.SecureCookie`
                        object)
        :param response: an instance of :attr:`response_class`
        """
        expires = None
        if session.permanent:
            expires = datetime.utcnow() + self.permanent_session_lifetime
        session.save_cookie(response, self.session_cookie_name,
                            expires=expires, httponly=True)

    def register_module(self, module, **options):
        """Registers a module with this application.  The keyword argument
        of this function are the same as the ones for the constructor of the
        :class:`Module` class and will override the values of the module if
        provided.
        """
        options.setdefault('url_prefix', module.url_prefix)
        state = _ModuleSetupState(self, **options)
        for func in module._register_events:
            func(state)

    def add_url_rule(self, rule, endpoint=None, view_func=None, **options):
        """Connects a URL rule.  Works exactly like the :meth:`route`
        decorator.  If a view_func is provided it will be registered with the
        endpoint.

        Basically this example::

            @app.route('/')
            def index():
                pass

        Is equivalent to the following::

            def index():
                pass
            app.add_url_rule('/', 'index', index)

        If the view_func is not provided you will need to connect the endpoint
        to a view function like so::

            app.view_functions['index'] = index

        .. versionchanged:: 0.2
           `view_func` parameter added.

        :param rule: the URL rule as string
        :param endpoint: the endpoint for the registered URL rule.  Flask
                         itself assumes the name of the view function as
                         endpoint
        :param view_func: the function to call when serving a request to the
                          provided endpoint
        :param options: the options to be forwarded to the underlying
                        :class:`~werkzeug.routing.Rule` object
        """
        if endpoint is None:
            assert view_func is not None, 'expected view func if endpoint ' \
                                          'is not provided.'
            endpoint = view_func.__name__
        options['endpoint'] = endpoint
        options.setdefault('methods', ('GET',))
        self.url_map.add(Rule(rule, **options))
        if view_func is not None:
            self.view_functions[endpoint] = view_func

    def route(self, rule, **options):
        """A decorator that is used to register a view function for a
        given URL rule.  Example::

            @app.route('/')
            def index():
                return 'Hello World'

        Variables parts in the route can be specified with angular
        brackets (``/user/<username>``).  By default a variable part
        in the URL accepts any string without a slash however a different
        converter can be specified as well by using ``<converter:name>``.

        Variable parts are passed to the view function as keyword
        arguments.

        The following converters are possible:

        =========== ===========================================
        `int`       accepts integers
        `float`     like `int` but for floating point values
        `path`      like the default but also accepts slashes
        =========== ===========================================

        Here some examples::

            @app.route('/')
            def index():
                pass

            @app.route('/<username>')
            def show_user(username):
                pass

            @app.route('/post/<int:post_id>')
            def show_post(post_id):
                pass

        An important detail to keep in mind is how Flask deals with trailing
        slashes.  The idea is to keep each URL unique so the following rules
        apply:

        1. If a rule ends with a slash and is requested without a slash
           by the user, the user is automatically redirected to the same
           page with a trailing slash attached.
        2. If a rule does not end with a trailing slash and the user request
           the page with a trailing slash, a 404 not found is raised.

        This is consistent with how web servers deal with static files.  This
        also makes it possible to use relative link targets safely.

        The :meth:`route` decorator accepts a couple of other arguments
        as well:

        :param rule: the URL rule as string
        :param methods: a list of methods this rule should be limited
                        to (``GET``, ``POST`` etc.).  By default a rule
                        just listens for ``GET`` (and implicitly ``HEAD``).
        :param subdomain: specifies the rule for the subdoain in case
                          subdomain matching is in use.
        :param strict_slashes: can be used to disable the strict slashes
                               setting for this rule.  See above.
        :param options: other options to be forwarded to the underlying
                        :class:`~werkzeug.routing.Rule` object.
        """
        def decorator(f):
            self.add_url_rule(rule, None, f, **options)
            return f
        return decorator

    def errorhandler(self, code):
        """A decorator that is used to register a function give a given
        error code.  Example::

            @app.errorhandler(404)
            def page_not_found():
                return 'This page does not exist', 404

        You can also register a function as error handler without using
        the :meth:`errorhandler` decorator.  The following example is
        equivalent to the one above::

            def page_not_found():
                return 'This page does not exist', 404
            app.error_handlers[404] = page_not_found

        :param code: the code as integer for the handler
        """
        def decorator(f):
            self.error_handlers[code] = f
            return f
        return decorator

    def template_filter(self, name=None):
        """A decorator that is used to register custom template filter.
        You can specify a name for the filter, otherwise the function
        name will be used. Example::

          @app.template_filter()
          def reverse(s):
              return s[::-1]

        :param name: the optional name of the filter, otherwise the
                     function name will be used.
        """
        def decorator(f):
            self.jinja_env.filters[name or f.__name__] = f
            return f
        return decorator

    def before_request(self, f):
        """Registers a function to run before each request."""
        self.before_request_funcs.setdefault(None, []).append(f)
        return f

    def after_request(self, f):
        """Register a function to be run after each request."""
        self.after_request_funcs.setdefault(None, []).append(f)
        return f

    def context_processor(self, f):
        """Registers a template context processor function."""
        self.template_context_processors[None].append(f)
        return f

    def dispatch_request(self):
        """Does the request dispatching.  Matches the URL and returns the
        return value of the view or error handler.  This does not have to
        be a response object.  In order to convert the return value to a
        proper response object, call :func:`make_response`.
        """
        req = _request_ctx_stack.top.request
        try:
            if req.routing_exception is not None:
                raise req.routing_exception
            return self.view_functions[req.endpoint](**req.view_args)
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

        The following types are allowed for `rv`:

        ======================= ===========================================
        :attr:`response_class`  the object is returned unchanged
        :class:`str`            a response object is created with the
                                string as body
        :class:`unicode`        a response object is created with the
                                string encoded to utf-8 as body
        :class:`tuple`          the response object is created with the
                                contents of the tuple as arguments
        a WSGI function         the function is called as WSGI application
                                and buffered as response object
        ======================= ===========================================

        :param rv: the return value from the view function
        """
        if rv is None:
            raise ValueError('View function did not return a response')
        if isinstance(rv, self.response_class):
            return rv
        if isinstance(rv, basestring):
            return self.response_class(rv)
        if isinstance(rv, tuple):
            return self.response_class(*rv)
        return self.response_class.force_type(rv, request.environ)

    def preprocess_request(self):
        """Called before the actual request dispatching and will
        call every as :meth:`before_request` decorated function.
        If any of these function returns a value it's handled as
        if it was the return value from the view and further
        request handling is stopped.
        """
        funcs = self.before_request_funcs.get(None, ())
        mod = request.module
        if mod and mod in self.before_request_funcs:
            funcs = chain(funcs, self.before_request_funcs[mod])
        for func in funcs:
            rv = func()
            if rv is not None:
                return rv

    def process_response(self, response):
        """Can be overridden in order to modify the response object
        before it's sent to the WSGI server.  By default this will
        call all the :meth:`after_request` decorated functions.

        :param response: a :attr:`response_class` object.
        :return: a new response object or the same, has to be an
                 instance of :attr:`response_class`.
        """
        ctx = _request_ctx_stack.top
        mod = ctx.request.module
        if not isinstance(ctx.session, _NullSession):
            self.save_session(ctx.session, response)
        funcs = ()
        if mod and mod in self.after_request_funcs:
            funcs = chain(funcs, self.after_request_funcs[mod])
        if None in self.after_request_funcs:
            funcs = chain(funcs, self.after_request_funcs[None])
        for handler in funcs:
            response = handler(response)
        return response

    def wsgi_app(self, environ, start_response):
        """The actual WSGI application.  This is not implemented in
        `__call__` so that middlewares can be applied without losing a
        reference to the class.  So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.wsgi_app = MyMiddleware(app.wsgi_app)

        Then you still have the original application object around and
        can continue to call methods on it.

        :param environ: a WSGI environment
        :param start_response: a callable accepting a status code,
                               a list of headers and an optional
                               exception context to start the response
        """
        with self.request_context(environ):
            rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request()
            response = self.make_response(rv)
            response = self.process_response(response)
            return response(environ, start_response)

    def request_context(self, environ):
        """Creates a request context from the given environment and binds
        it to the current context.  This must be used in combination with
        the `with` statement because the request is only bound to the
        current context for the duration of the `with` block.

        Example usage::

            with app.request_context(environ):
                do_something_with(request)

        :params environ: a WSGI environment
        """
        return _RequestContext(self, environ)

    def test_request_context(self, *args, **kwargs):
        """Creates a WSGI environment from the given values (see
        :func:`werkzeug.create_environ` for more information, this
        function accepts the same arguments).
        """
        return self.request_context(create_environ(*args, **kwargs))

    def __call__(self, environ, start_response):
        """Shortcut for :attr:`wsgi_app`."""
        return self.wsgi_app(environ, start_response)


# context locals
_request_ctx_stack = LocalStack()
current_app = LocalProxy(lambda: _request_ctx_stack.top.app)
request = LocalProxy(lambda: _request_ctx_stack.top.request)
session = LocalProxy(lambda: _request_ctx_stack.top.session)
g = LocalProxy(lambda: _request_ctx_stack.top.g)
