# -*- coding: utf-8 -*-
"""
    flask.app
    ~~~~~~~~~

    This module implements the central WSGI application object.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from __future__ import with_statement

import sys
from threading import Lock
from datetime import timedelta, datetime
from itertools import chain

from werkzeug import ImmutableDict
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, InternalServerError, \
     MethodNotAllowed

from .helpers import _PackageBoundObject, url_for, get_flashed_messages, \
    locked_cached_property, _tojson_filter, _endpoint_from_view_func
from .wrappers import Request, Response
from .config import ConfigAttribute, Config
from .ctx import RequestContext
from .globals import _request_ctx_stack, request
from .session import Session, _NullSession
from .module import blueprint_is_module
from .templating import DispatchingJinjaLoader, Environment, \
    _default_template_ctx_processor
from .signals import request_started, request_finished, got_request_exception, \
    request_tearing_down

# a lock used for logger initialization
_logger_lock = Lock()


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

    .. admonition:: About the First Parameter

        The idea of the first parameter is to give Flask an idea what
        belongs to your application.  This name is used to find resources
        on the file system, can be used by extensions to improve debugging
        information and a lot more.

        So it's important what you provide there.  If you are using a single
        module, `__name__` is always the correct value.  If you however are
        using a package, it's usually recommended to hardcode the name of
        your package there.

        For example if your application is defined in `yourapplication/app.py`
        you should create it with one of the two versions below::

            app = Flask('yourapplication')
            app = Flask(__name__.split('.')[0])

        Why is that?  The application will work even with `__name__`, thanks
        to how resources are looked up.  However it will make debugging more
        painful.  Certain extensions can make assumptions based on the
        import name of your application.  For example the Flask-SQLAlchemy
        extension will look for the code in your application that triggered
        an SQL query in debug mode.  If the import name is not properly set
        up, that debugging information is lost.  (For example it would only
        pick up SQL queries in `yourapplicaiton.app` and not
        `yourapplication.views.frontend`)

    .. versionadded:: 0.5
       The `static_path` parameter was added.

    :param import_name: the name of the application package
    :param static_path: can be used to specify a different path for the
                        static files on the web.  Defaults to ``/static``.
                        This does not affect the folder the files are served
                        *from*.
    """

    #: The class that is used for request objects.  See :class:`~flask.Request`
    #: for more information.
    request_class = Request

    #: The class that is used for response objects.  See
    #: :class:`~flask.Response` for more information.
    response_class = Response

    #: The debug flag.  Set this to `True` to enable debugging of the
    #: application.  In debug mode the debugger will kick in when an unhandled
    #: exception ocurrs and the integrated server will automatically reload
    #: the application if changes in the code are detected.
    #:
    #: This attribute can also be configured from the config with the `DEBUG`
    #: configuration key.  Defaults to `False`.
    debug = ConfigAttribute('DEBUG')

    #: The testing flask.  Set this to `True` to enable the test mode of
    #: Flask extensions (and in the future probably also Flask itself).
    #: For example this might activate unittest helpers that have an
    #: additional runtime cost which should not be enabled by default.
    #:
    #: If this is enabled and PROPAGATE_EXCEPTIONS is not changed from the
    #: default it's implicitly enabled.
    #:
    #: This attribute can also be configured from the config with the
    #: `TESTING` configuration key.  Defaults to `False`.
    testing = ConfigAttribute('TESTING')

    #: If a secret key is set, cryptographic components can use this to
    #: sign cookies and other things.  Set this to a complex random value
    #: when you want to use the secure cookie for instance.
    #:
    #: This attribute can also be configured from the config with the
    #: `SECRET_KEY` configuration key.  Defaults to `None`.
    secret_key = ConfigAttribute('SECRET_KEY')

    #: The secure cookie uses this for the name of the session cookie.
    #:
    #: This attribute can also be configured from the config with the
    #: `SESSION_COOKIE_NAME` configuration key.  Defaults to ``'session'``
    session_cookie_name = ConfigAttribute('SESSION_COOKIE_NAME')

    #: A :class:`~datetime.timedelta` which is used to set the expiration
    #: date of a permanent session.  The default is 31 days which makes a
    #: permanent session survive for roughly one month.
    #:
    #: This attribute can also be configured from the config with the
    #: `PERMANENT_SESSION_LIFETIME` configuration key.  Defaults to
    #: ``timedelta(days=31)``
    permanent_session_lifetime = ConfigAttribute('PERMANENT_SESSION_LIFETIME')

    #: Enable this if you want to use the X-Sendfile feature.  Keep in
    #: mind that the server has to support this.  This only affects files
    #: sent with the :func:`send_file` method.
    #:
    #: .. versionadded:: 0.2
    #:
    #: This attribute can also be configured from the config with the
    #: `USE_X_SENDFILE` configuration key.  Defaults to `False`.
    use_x_sendfile = ConfigAttribute('USE_X_SENDFILE')

    #: The name of the logger to use.  By default the logger name is the
    #: package name passed to the constructor.
    #:
    #: .. versionadded:: 0.4
    logger_name = ConfigAttribute('LOGGER_NAME')

    #: Enable the deprecated module support?  This is active by default
    #: in 0.7 but will be changed to False in 0.8.  With Flask 1.0 modules
    #: will be removed in favor of Blueprints
    enable_modules = True

    #: The logging format used for the debug logger.  This is only used when
    #: the application is in debug mode, otherwise the attached logging
    #: handler does the formatting.
    #:
    #: .. versionadded:: 0.3
    debug_log_format = (
        '-' * 80 + '\n' +
        '%(levelname)s in %(module)s [%(pathname)s:%(lineno)d]:\n' +
        '%(message)s\n' +
        '-' * 80
    )

    #: Options that are passed directly to the Jinja2 environment.
    jinja_options = ImmutableDict(
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_']
    )

    #: Default configuration parameters.
    default_config = ImmutableDict({
        'DEBUG':                                False,
        'TESTING':                              False,
        'PROPAGATE_EXCEPTIONS':                 None,
        'PRESERVE_CONTEXT_ON_EXCEPTION':        None,
        'SECRET_KEY':                           None,
        'SESSION_COOKIE_NAME':                  'session',
        'PERMANENT_SESSION_LIFETIME':           timedelta(days=31),
        'USE_X_SENDFILE':                       False,
        'LOGGER_NAME':                          None,
        'SERVER_NAME':                          None,
        'MAX_CONTENT_LENGTH':                   None
    })

    #: The rule object to use for URL rules created.  This is used by
    #: :meth:`add_url_rule`.  Defaults to :class:`werkzeug.routing.Rule`.
    #:
    #: .. versionadded:: 0.7
    url_rule_class = Rule

    #: the test client that is used with when `test_client` is used.
    #:
    #: .. versionadded:: 0.7
    test_client_class = None

    def __init__(self, import_name, static_path=None, static_url_path=None,
                 static_folder='static', template_folder='templates'):
        _PackageBoundObject.__init__(self, import_name,
                                     template_folder=template_folder)
        if static_path is not None:
            from warnings import warn
            warn(DeprecationWarning('static_path is now called '
                                    'static_url_path'), stacklevel=2)
            static_url_path = static_path

        if static_url_path is not None:
            self.static_url_path = static_url_path
        if static_folder is not None:
            self.static_folder = static_folder

        #: The configuration dictionary as :class:`Config`.  This behaves
        #: exactly like a regular dictionary but supports additional methods
        #: to load a config from files.
        self.config = Config(self.root_path, self.default_config)

        #: Prepare the deferred setup of the logger.
        self._logger = None
        self.logger_name = self.import_name

        #: A dictionary of all view functions registered.  The keys will
        #: be function names which are also used to generate URLs and
        #: the values are the function objects themselves.
        #: To register a view function, use the :meth:`route` decorator.
        self.view_functions = {}

        # support for the now deprecated `error_handlers` attribute.  The
        # :attr:`error_handler_spec` shall be used now.
        self._error_handlers = {}

        #: A dictionary of all registered error handlers.  The key is `None`
        #: for error handlers active on the application, otherwise the key is
        #: the name of the blueprint.  Each key points to another dictionary
        #: where they key is the status code of the http exception.  The
        #: special key `None` points to a list of tuples where the first item
        #: is the class for the instance check and the second the error handler
        #: function.
        #:
        #: To register a error handler, use the :meth:`errorhandler`
        #: decorator.
        self.error_handler_spec = {None: self._error_handlers}

        #: A dictionary with lists of functions that should be called at the
        #: beginning of the request.  The key of the dictionary is the name of
        #: the blueprint this function is active for, `None` for all requests.
        #: This can for example be used to open database connections or
        #: getting hold of the currently logged in user.  To register a
        #: function here, use the :meth:`before_request` decorator.
        self.before_request_funcs = {}

        #: A dictionary with lists of functions that should be called after
        #: each request.  The key of the dictionary is the name of the blueprint
        #: this function is active for, `None` for all requests.  This can for
        #: example be used to open database connections or getting hold of the
        #: currently logged in user.  To register a function here, use the
        #: :meth:`after_request` decorator.
        self.after_request_funcs = {}

        #: A dictionary with lists of functions that are called after
        #: each request, even if an exception has occurred. The key of the
        #: dictionary is the name of the blueprint this function is active for,
        #: `None` for all requests. These functions are not allowed to modify
        #: the request, and their return values are ignored. If an exception
        #: occurred while processing the request, it gets passed to each
        #: teardown_request function. To register a function here, use the
        #: :meth:`teardown_request` decorator.
        #:
        #: .. versionadded:: 0.7
        self.teardown_request_funcs = {}

        #: A dictionary with lists of functions that can be used as URL
        #: value processor functions.  Whenever a URL is built these functions
        #: are called to modify the dictionary of values in place.  The key
        #: `None` here is used for application wide
        #: callbacks, otherwise the key is the name of the blueprint.
        #: Each of these functions has the chance to modify the dictionary
        #:
        #: .. versionadded:: 0.7
        self.url_value_preprocessors = {}

        #: A dictionary with lists of functions that can be used as URL value
        #: preprocessors.  The key `None` here is used for application wide
        #: callbacks, otherwise the key is the name of the blueprint.
        #: Each of these functions has the chance to modify the dictionary
        #: of URL values before they are used as the keyword arguments of the
        #: view function.  For each function registered this one should also
        #: provide a :meth:`url_defaults` function that adds the parameters
        #: automatically again that were removed that way.
        #:
        #: .. versionadded:: 0.7
        self.url_default_functions = {}

        #: A dictionary with list of functions that are called without argument
        #: to populate the template context.  The key of the dictionary is the
        #: name of the blueprint this function is active for, `None` for all
        #: requests.  Each returns a dictionary that the template context is
        #: updated with.  To register a function here, use the
        #: :meth:`context_processor` decorator.
        self.template_context_processors = {
            None: [_default_template_ctx_processor]
        }

        #: all the attached blueprints in a directory by name.  Blueprints
        #: can be attached multiple times so this dictionary does not tell
        #: you how often they got attached.
        #:
        #: .. versionadded:: 0.7
        self.blueprints = {}

        #: a place where extensions can store application specific state.  For
        #: example this is where an extension could store database engines and
        #: similar things.  For backwards compatibility extensions should register
        #: themselves like this::
        #:
        #:      if not hasattr(app, 'extensions'):
        #:          app.extensions = {}
        #:      app.extensions['extensionname'] = SomeObject()
        #:
        #: The key must match the name of the `flaskext` module.  For example in
        #: case of a "Flask-Foo" extension in `flaskext.foo`, the key would be
        #: ``'foo'``.
        #:
        #: .. versionadded:: 0.7
        self.extensions = {}

        #: The :class:`~werkzeug.routing.Map` for this instance.  You can use
        #: this to change the routing converters after the class was created
        #: but before any routes are connected.  Example::
        #:
        #:    from werkzeug.routing import BaseConverter
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

        # register the static folder for the application.  Do that even
        # if the folder does not exist.  First of all it might be created
        # while the server is running (usually happens during development)
        # but also because google appengine stores static files somewhere
        # else when mapped with the .yml file.
        if self.has_static_folder:
            self.add_url_rule(self.static_url_path + '/<path:filename>',
                              endpoint='static',
                              view_func=self.send_static_file)

    def _get_error_handlers(self):
        from warnings import warn
        warn(DeprecationWarning('error_handlers is deprecated, use the '
            'new error_handler_spec attribute instead.'), stacklevel=1)
        return self._error_handlers
    def _set_error_handlers(self, value):
        self._error_handlers = value
        self.error_handler_spec[None] = value
    error_handlers = property(_get_error_handlers, _set_error_handlers)
    del _get_error_handlers, _set_error_handlers

    @property
    def propagate_exceptions(self):
        """Returns the value of the `PROPAGATE_EXCEPTIONS` configuration
        value in case it's set, otherwise a sensible default is returned.

        .. versionadded:: 0.7
        """
        rv = self.config['PROPAGATE_EXCEPTIONS']
        if rv is not None:
            return rv
        return self.testing or self.debug

    @property
    def preserve_context_on_exception(self):
        """Returns the value of the `PRESERVE_CONTEXT_ON_EXCEPTION`
        configuration value in case it's set, otherwise a sensible default
        is returned.

        .. versionadded:: 0.7
        """
        rv = self.config['PRESERVE_CONTEXT_ON_EXCEPTION']
        if rv is not None:
            return rv
        return self.debug

    @property
    def logger(self):
        """A :class:`logging.Logger` object for this application.  The
        default configuration is to log to stderr if the application is
        in debug mode.  This logger can be used to (surprise) log messages.
        Here some examples::

            app.logger.debug('A value for debugging')
            app.logger.warning('A warning ocurred (%d apples)', 42)
            app.logger.error('An error occoured')

        .. versionadded:: 0.3
        """
        if self._logger and self._logger.name == self.logger_name:
            return self._logger
        with _logger_lock:
            if self._logger and self._logger.name == self.logger_name:
                return self._logger
            from flask.logging import create_logger
            self._logger = rv = create_logger(self)
            return rv

    @locked_cached_property
    def jinja_env(self):
        """The Jinja2 environment used to load templates."""
        rv = self.create_jinja_environment()

        # Hack to support the init_jinja_globals method which is supported
        # until 1.0 but has an API deficiency.
        if getattr(self.init_jinja_globals, 'im_func', None) is not \
           Flask.init_jinja_globals.im_func:
            from warnings import warn
            warn(DeprecationWarning('This flask class uses a customized '
                'init_jinja_globals() method which is deprecated. '
                'Move the code from that method into the '
                'create_jinja_environment() method instead.'))
            self.__dict__['jinja_env'] = rv
            self.init_jinja_globals()

        return rv

    def create_jinja_environment(self):
        """Creates the Jinja2 environment based on :attr:`jinja_options`
        and :meth:`select_jinja_autoescape`.  Since 0.7 this also adds
        the Jinja2 globals and filters after initialization.  Override
        this function to customize the behavior.

        .. versionadded:: 0.5
        """
        options = dict(self.jinja_options)
        if 'autoescape' not in options:
            options['autoescape'] = self.select_jinja_autoescape
        rv = Environment(self, **options)
        rv.globals.update(
            url_for=url_for,
            get_flashed_messages=get_flashed_messages
        )
        rv.filters['tojson'] = _tojson_filter
        return rv

    def create_global_jinja_loader(self):
        """Creates the loader for the Jinja2 environment.  Can be used to
        override just the loader and keeping the rest unchanged.  It's
        discouraged to override this function.  Instead one should override
        the :meth:`create_jinja_loader` function instead.

        The global loader dispatches between the loaders of the application
        and the individual blueprints.

        .. versionadded:: 0.7
        """
        return DispatchingJinjaLoader(self)

    def init_jinja_globals(self):
        """Deprecated.  Used to initialize the Jinja2 globals.

        .. versionadded:: 0.5
        .. versionchanged:: 0.7
           This method is deprecated with 0.7.  Override
           :meth:`create_jinja_environment` instead.
        """

    def select_jinja_autoescape(self, filename):
        """Returns `True` if autoescaping should be active for the given
        template name.

        .. versionadded:: 0.5
        """
        if filename is None:
            return False
        return filename.endswith(('.html', '.htm', '.xml', '.xhtml'))

    def update_template_context(self, context):
        """Update the template context with some commonly used variables.
        This injects request, session, config and g into the template
        context as well as everything template context processors want
        to inject.  Note that the as of Flask 0.6, the original values
        in the context will not be overriden if a context processor
        decides to return a value with the same key.

        :param context: the context as a dictionary that is updated in place
                        to add extra variables.
        """
        funcs = self.template_context_processors[None]
        bp = _request_ctx_stack.top.request.blueprint
        if bp is not None and bp in self.template_context_processors:
            funcs = chain(funcs, self.template_context_processors[bp])
        orig_ctx = context.copy()
        for func in funcs:
            context.update(func())
        # make sure the original values win.  This makes it possible to
        # easier add new variables in context processors without breaking
        # existing views.
        context.update(orig_ctx)

    def run(self, host='127.0.0.1', port=5000, **options):
        """Runs the application on a local development server.  If the
        :attr:`debug` flag is set the server will automatically reload
        for code changes and show a debugger in case an exception happened.

        If you want to run the application in debug mode, but disable the
        code execution on the interactive debugger, you can pass
        ``use_evalex=False`` as parameter.  This will keep the debugger's
        traceback screen active, but disable code execution.

        .. admonition:: Keep in Mind

           Flask will suppress any server error with a generic error page
           unless it is in debug mode.  As such to enable just the
           interactive debugger without the code reloading, you have to
           invoke :meth:`run` with ``debug=True`` and ``use_reloader=False``.
           Setting ``use_debugger`` to `True` without being in debug mode
           won't catch any exceptions because there won't be any to
           catch.

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

    def test_client(self, use_cookies=True):
        """Creates a test client for this application.  For information
        about unit testing head over to :ref:`testing`.

        The test client can be used in a `with` block to defer the closing down
        of the context until the end of the `with` block.  This is useful if
        you want to access the context locals for testing::

            with app.test_client() as c:
                rv = c.get('/?vodka=42')
                assert request.args['vodka'] == '42'

        .. versionchanged:: 0.4
           added support for `with` block usage for the client.

        .. versionadded:: 0.7
           The `use_cookies` parameter was added as well as the ability
           to override the client to be used by setting the
           :attr:`test_client_class` attribute.
        """
        cls = self.test_client_class
        if cls is None:
            from flask.testing import FlaskClient as cls
        return cls(self, self.response_class, use_cookies=use_cookies)

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
        expires = domain = None
        if session.permanent:
            expires = datetime.utcnow() + self.permanent_session_lifetime
        if self.config['SERVER_NAME'] is not None:
            # chop of the port which is usually not supported by browsers
            domain = '.' + self.config['SERVER_NAME'].rsplit(':', 1)[0]
        session.save_cookie(response, self.session_cookie_name,
                            expires=expires, httponly=True, domain=domain)

    def register_module(self, module, **options):
        """Registers a module with this application.  The keyword argument
        of this function are the same as the ones for the constructor of the
        :class:`Module` class and will override the values of the module if
        provided.

        .. versionchanged:: 0.7
           The module system was deprecated in favor for the blueprint
           system.
        """
        assert blueprint_is_module(module), 'register_module requires ' \
            'actual module objects.  Please upgrade to blueprints though.'
        if not self.enable_modules:
            raise RuntimeError('Module support was disabled but code '
                'attempted to register a module named %r' % module)
        else:
            from warnings import warn
            warn(DeprecationWarning('Modules are deprecated.  Upgrade to '
                'using blueprints.  Have a look into the documentation for '
                'more information.  If this module was registered by a '
                'Flask-Extension upgrade the extension or contact the author '
                'of that extension instead.  (Registered %r)' % module),
                stacklevel=2)

        self.register_blueprint(module, **options)

    def register_blueprint(self, blueprint, **options):
        """Registers a blueprint on the application.

        .. versionadded:: 0.7
        """
        first_registration = False
        if blueprint.name in self.blueprints:
            assert self.blueprints[blueprint.name] is blueprint, \
                'A blueprint\'s name collision ocurred between %r and ' \
                '%r.  Both share the same name "%s".  Blueprints that ' \
                'are created on the fly need unique names.' % \
                (blueprint, self.blueprints[blueprint.name], blueprint.name)
        else:
            self.blueprints[blueprint.name] = blueprint
            first_registration = True
        blueprint.register(self, options, first_registration)

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

        .. versionchanged:: 0.6
           `OPTIONS` is added automatically as method.

        :param rule: the URL rule as string
        :param endpoint: the endpoint for the registered URL rule.  Flask
                         itself assumes the name of the view function as
                         endpoint
        :param view_func: the function to call when serving a request to the
                          provided endpoint
        :param options: the options to be forwarded to the underlying
                        :class:`~werkzeug.routing.Rule` object.  A change
                        to Werkzeug is handling of method options.  methods
                        is a list of methods this rule should be limited
                        to (`GET`, `POST` etc.).  By default a rule
                        just listens for `GET` (and implicitly `HEAD`).
                        Starting with Flask 0.6, `OPTIONS` is implicitly
                        added and handled by the standard request handling.
        """
        if endpoint is None:
            endpoint = _endpoint_from_view_func(view_func)
        options['endpoint'] = endpoint
        methods = options.pop('methods', None)
        # if the methods are not given and the view_func object knows its
        # methods we can use that instead.  If neither exists, we go with
        # a tuple of only `GET` as default.
        if methods is None:
            methods = getattr(view_func, 'methods', None) or ('GET',)
        provide_automatic_options = False
        if 'OPTIONS' not in methods:
            methods = tuple(methods) + ('OPTIONS',)
            provide_automatic_options = True

        # due to a werkzeug bug we need to make sure that the defaults are
        # None if they are an empty dictionary.  This should not be necessary
        # with Werkzeug 0.7
        options['defaults'] = options.get('defaults') or None

        rule = self.url_rule_class(rule, methods=methods, **options)
        rule.provide_automatic_options = provide_automatic_options
        self.url_map.add(rule)
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
                        to (`GET`, `POST` etc.).  By default a rule
                        just listens for `GET` (and implicitly `HEAD`).
                        Starting with Flask 0.6, `OPTIONS` is implicitly
                        added and handled by the standard request handling.
        :param subdomain: specifies the rule for the subdomain in case
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

    def endpoint(self, endpoint):
        """A decorator to register a function as an endpoint.
        Example::

            @app.endpoint('example.endpoint')
            def example():
                return "example"

        :param endpoint: the name of the endpoint
        """
        def decorator(f):
            self.view_functions[endpoint] = f
            return f
        return decorator

    def errorhandler(self, code_or_exception):
        """A decorator that is used to register a function give a given
        error code.  Example::

            @app.errorhandler(404)
            def page_not_found(error):
                return 'This page does not exist', 404

        You can also register handlers for arbitrary exceptions::

            @app.errorhandler(DatabaseError)
            def special_exception_handler(error):
                return 'Database connection failed', 500

        You can also register a function as error handler without using
        the :meth:`errorhandler` decorator.  The following example is
        equivalent to the one above::

            def page_not_found(error):
                return 'This page does not exist', 404
            app.error_handler_spec[None][404] = page_not_found

        Setting error handlers via assignments to :attr:`error_handler_spec`
        however is discouraged as it requires fidling with nested dictionaries
        and the special case for arbitrary exception types.

        The first `None` refers to the active blueprint.  If the error
        handler should be application wide `None` shall be used.

        .. versionadded:: 0.7
           One can now additionally also register custom exception types
           that do not necessarily have to be a subclass of the
           :class:~`werkzeug.exceptions.HTTPException` class.

        :param code: the code as integer for the handler
        """
        def decorator(f):
            self._register_error_handler(None, code_or_exception, f)
            return f
        return decorator

    def register_error_handler(self, code_or_exception, f):
        """Alternative error attach function to the :meth:`errorhandler`
        decorator that is more straightforward to use for non decorator
        usage.

        .. versionadded:: 0.7
        """
        self._register_error_handler(None, code_or_exception, f)

    def _register_error_handler(self, key, code_or_exception, f):
        if isinstance(code_or_exception, HTTPException):
            code_or_exception = code_or_exception.code
        if isinstance(code_or_exception, (int, long)):
            assert code_or_exception != 500 or key is None, \
                'It is currently not possible to register a 500 internal ' \
                'server error on a per-blueprint level.'
            self.error_handler_spec.setdefault(key, {})[code_or_exception] = f
        else:
            self.error_handler_spec.setdefault(key, {}).setdefault(None, []) \
                .append((code_or_exception, f))

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
        """Register a function to be run after each request.  Your function
        must take one parameter, a :attr:`response_class` object and return
        a new response object or the same (see :meth:`process_response`).

        As of Flask 0.7 this function might not be executed at the end of the
        request in case an unhandled exception ocurred.
        """
        self.after_request_funcs.setdefault(None, []).append(f)
        return f

    def teardown_request(self, f):
        """Register a function to be run at the end of each request,
        regardless of whether there was an exception or not.  These functions
        are executed when the request context is popped, even if not an
        actual request was performed.

        Example::

            ctx = app.test_request_context()
            ctx.push()
            ...
            ctx.pop()

        When ``ctx.pop()`` is executed in the above example, the teardown
        functions are called just before the request context moves from the
        stack of active contexts.  This becomes relevant if you are using
        such constructs in tests.

        Generally teardown functions must take every necesary step to avoid
        that they will fail.  If they do execute code that might fail they
        will have to surround the execution of these code by try/except
        statements and log ocurring errors.
        """
        self.teardown_request_funcs.setdefault(None, []).append(f)
        return f

    def context_processor(self, f):
        """Registers a template context processor function."""
        self.template_context_processors[None].append(f)
        return f

    def url_value_preprocessor(self, f):
        """Registers a function as URL value preprocessor for all view
        functions of the application.  It's called before the view functions
        are called and can modify the url values provided.
        """
        self.url_value_preprocessors.setdefault(None, []).append(f)
        return f

    def url_defaults(self, f):
        """Callback function for URL defaults for all view functions of the
        application.  It's called with the endpoint and values and should
        update the values passed in place.
        """
        self.url_default_functions.setdefault(None, []).append(f)
        return f

    def handle_http_exception(self, e):
        """Handles an HTTP exception.  By default this will invoke the
        registered error handlers and fall back to returning the
        exception as response.

        .. versionadded: 0.3
        """
        handlers = self.error_handler_spec.get(request.blueprint)
        if handlers and e.code in handlers:
            handler = handlers[e.code]
        else:
            handler = self.error_handler_spec[None].get(e.code)
        if handler is None:
            return e
        return handler(e)

    def handle_user_exception(self, e):
        """This method is called whenever an exception occurs that should be
        handled.  A special case are
        :class:`~werkzeug.exception.HTTPException`\s which are forwarded by
        this function to the :meth:`handle_http_exception` method.  This
        function will either return a response value or reraise the
        exception with the same traceback.

        .. versionadded:: 0.7
        """
        # ensure not to trash sys.exc_info() at that point in case someone
        # wants the traceback preserved in handle_http_exception.
        if isinstance(e, HTTPException):
            return self.handle_http_exception(e)

        exc_type, exc_value, tb = sys.exc_info()
        assert exc_value is e

        blueprint_handlers = ()
        handlers = self.error_handler_spec.get(request.blueprint)
        if handlers is not None:
            blueprint_handlers = handlers.get(None, ())
        app_handlers = self.error_handler_spec[None].get(None, ())
        for typecheck, handler in chain(blueprint_handlers, app_handlers):
            if isinstance(e, typecheck):
                return handler(e)

        raise exc_type, exc_value, tb

    def handle_exception(self, e):
        """Default exception handling that kicks in when an exception
        occours that is not caught.  In debug mode the exception will
        be re-raised immediately, otherwise it is logged and the handler
        for a 500 internal server error is used.  If no such handler
        exists, a default 500 internal server error message is displayed.

        .. versionadded: 0.3
        """
        exc_type, exc_value, tb = sys.exc_info()

        got_request_exception.send(self, exception=e)
        handler = self.error_handler_spec[None].get(500)

        if self.propagate_exceptions:
            # if we want to repropagate the exception, we can attempt to
            # raise it with the whole traceback in case we can do that
            # (the function was actually called from the except part)
            # otherwise, we just raise the error again
            if exc_value is e:
                raise exc_type, exc_value, tb
            else:
                raise e

        self.logger.exception('Exception on %s [%s]' % (
            request.path,
            request.method
        ))
        if handler is None:
            return InternalServerError()
        return handler(e)

    def dispatch_request(self):
        """Does the request dispatching.  Matches the URL and returns the
        return value of the view or error handler.  This does not have to
        be a response object.  In order to convert the return value to a
        proper response object, call :func:`make_response`.

        .. versionchanged:: 0.7
           This no longer does the exception handling, this code was
           moved to the new :meth:`full_dispatch_request`.
        """
        req = _request_ctx_stack.top.request
        if req.routing_exception is not None:
            raise req.routing_exception
        rule = req.url_rule
        # if we provide automatic options for this URL and the
        # request came with the OPTIONS method, reply automatically
        if getattr(rule, 'provide_automatic_options', False) \
           and req.method == 'OPTIONS':
            return self.make_default_options_response()
        # otherwise dispatch to the handler for that endpoint
        return self.view_functions[rule.endpoint](**req.view_args)

    def full_dispatch_request(self):
        """Dispatches the request and on top of that performs request
        pre and postprocessing as well as HTTP exception catching and
        error handling.

        .. versionadded:: 0.7
        """
        try:
            request_started.send(self)
            rv = self.preprocess_request()
            if rv is None:
                rv = self.dispatch_request()
        except Exception, e:
            rv = self.handle_user_exception(e)
        response = self.make_response(rv)
        response = self.process_response(response)
        request_finished.send(self, response=response)
        return response

    def make_default_options_response(self):
        """This method is called to create the default `OPTIONS` response.
        This can be changed through subclassing to change the default
        behaviour of `OPTIONS` responses.

        .. versionadded:: 0.7
        """
        # This would be nicer in Werkzeug 0.7, which however currently
        # is not released.  Werkzeug 0.7 provides a method called
        # allowed_methods() that returns all methods that are valid for
        # a given path.
        methods = []
        try:
            _request_ctx_stack.top.url_adapter.match(method='--')
        except MethodNotAllowed, e:
            methods = e.valid_methods
        except HTTPException, e:
            pass
        rv = self.response_class()
        rv.allow.update(methods)
        return rv

    def make_response(self, rv):
        """Converts the return value from a view function to a real
        response object that is an instance of :attr:`response_class`.

        The following types are allowed for `rv`:

        .. tabularcolumns:: |p{3.5cm}|p{9.5cm}|

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

    def create_url_adapter(self, request):
        """Creates a URL adapter for the given request.  The URL adapter
        is created at a point where the request context is not yet set up
        so the request is passed explicitly.

        .. versionadded:: 0.6
        """
        return self.url_map.bind_to_environ(request.environ,
            server_name=self.config['SERVER_NAME'])

    def inject_url_defaults(self, endpoint, values):
        """Injects the URL defaults for the given endpoint directly into
        the values dictionary passed.  This is used internally and
        automatically called on URL building.

        .. versionadded:: 0.7
        """
        funcs = self.url_default_functions.get(None, ())
        if '.' in endpoint:
            bp = endpoint.split('.', 1)[0]
            funcs = chain(funcs, self.url_default_functions.get(bp, ()))
        for func in funcs:
            func(endpoint, values)

    def preprocess_request(self):
        """Called before the actual request dispatching and will
        call every as :meth:`before_request` decorated function.
        If any of these function returns a value it's handled as
        if it was the return value from the view and further
        request handling is stopped.

        This also triggers the :meth:`url_value_processor` functions before
        the actualy :meth:`before_request` functions are called.
        """
        bp = request.blueprint

        funcs = self.url_value_preprocessors.get(None, ())
        if bp is not None and bp in self.url_value_preprocessors:
            funcs = chain(funcs, self.url_value_preprocessors[bp])
        for func in funcs:
            func(request.endpoint, request.view_args)

        funcs = self.before_request_funcs.get(None, ())
        if bp is not None and bp in self.before_request_funcs:
            funcs = chain(funcs, self.before_request_funcs[bp])
        for func in funcs:
            rv = func()
            if rv is not None:
                return rv

    def process_response(self, response):
        """Can be overridden in order to modify the response object
        before it's sent to the WSGI server.  By default this will
        call all the :meth:`after_request` decorated functions.

        .. versionchanged:: 0.5
           As of Flask 0.5 the functions registered for after request
           execution are called in reverse order of registration.

        :param response: a :attr:`response_class` object.
        :return: a new response object or the same, has to be an
                 instance of :attr:`response_class`.
        """
        ctx = _request_ctx_stack.top
        bp = ctx.request.blueprint
        if not isinstance(ctx.session, _NullSession):
            self.save_session(ctx.session, response)
        funcs = ()
        if bp is not None and bp in self.after_request_funcs:
            funcs = reversed(self.after_request_funcs[bp])
        if None in self.after_request_funcs:
            funcs = chain(funcs, reversed(self.after_request_funcs[None]))
        for handler in funcs:
            response = handler(response)
        return response

    def do_teardown_request(self):
        """Called after the actual request dispatching and will
        call every as :meth:`teardown_request` decorated function.  This is
        not actually called by the :class:`Flask` object itself but is always
        triggered when the request context is popped.  That way we have a
        tighter control over certain resources under testing environments.
        """
        funcs = reversed(self.teardown_request_funcs.get(None, ()))
        bp = request.blueprint
        if bp is not None and bp in self.teardown_request_funcs:
            funcs = chain(funcs, reversed(self.teardown_request_funcs[bp]))
        exc = sys.exc_info()[1]
        for func in funcs:
            rv = func(exc)
            if rv is not None:
                return rv
        request_tearing_down.send(self)

    def request_context(self, environ):
        """Creates a :class:`~flask.ctx.RequestContext` from the given
        environment and binds it to the current context.  This must be used in
        combination with the `with` statement because the request is only bound
        to the current context for the duration of the `with` block.

        Example usage::

            with app.request_context(environ):
                do_something_with(request)

        The object returned can also be used without the `with` statement
        which is useful for working in the shell.  The example above is
        doing exactly the same as this code::

            ctx = app.request_context(environ)
            ctx.push()
            try:
                do_something_with(request)
            finally:
                ctx.pop()

        .. versionchanged:: 0.3
           Added support for non-with statement usage and `with` statement
           is now passed the ctx object.

        :param environ: a WSGI environment
        """
        return RequestContext(self, environ)

    def test_request_context(self, *args, **kwargs):
        """Creates a WSGI environment from the given values (see
        :func:`werkzeug.create_environ` for more information, this
        function accepts the same arguments).
        """
        from werkzeug import create_environ
        environ_overrides = kwargs.setdefault('environ_overrides', {})
        if self.config.get('SERVER_NAME'):
            server_name = self.config.get('SERVER_NAME')
            if ':' not in server_name:
                http_host, http_port = server_name, '80'
            else:
                http_host, http_port = server_name.split(':', 1)

            environ_overrides.setdefault('SERVER_NAME', server_name)
            environ_overrides.setdefault('HTTP_HOST', server_name)
            environ_overrides.setdefault('SERVER_PORT', http_port)
        return self.request_context(create_environ(*args, **kwargs))

    def wsgi_app(self, environ, start_response):
        """The actual WSGI application.  This is not implemented in
        `__call__` so that middlewares can be applied without losing a
        reference to the class.  So instead of doing this::

            app = MyMiddleware(app)

        It's a better idea to do this instead::

            app.wsgi_app = MyMiddleware(app.wsgi_app)

        Then you still have the original application object around and
        can continue to call methods on it.

        .. versionchanged:: 0.7
           The behavior of the before and after request callbacks was changed
           under error conditions and a new callback was added that will
           always execute at the end of the request, independent on if an
           error ocurred or not.  See :ref:`callbacks-and-errors`.

        :param environ: a WSGI environment
        :param start_response: a callable accepting a status code,
                               a list of headers and an optional
                               exception context to start the response
        """
        with self.request_context(environ):
            try:
                response = self.full_dispatch_request()
            except Exception, e:
                response = self.make_response(self.handle_exception(e))
            return response(environ, start_response)

    @property
    def modules(self):
        from warnings import warn
        warn(DeprecationWarning('Flask.modules is deprecated, use '
                                'Flask.blueprints instead'), stacklevel=2)
        return self.blueprints

    def __call__(self, environ, start_response):
        """Shortcut for :attr:`wsgi_app`."""
        return self.wsgi_app(environ, start_response)
