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
import mimetypes
from datetime import datetime, timedelta

# this is a workaround for appengine.  Do not remove this import
import werkzeug

from itertools import chain
from threading import Lock
from jinja2 import Environment, PackageLoader, FileSystemLoader
from werkzeug import Request as RequestBase, Response as ResponseBase, \
     LocalStack, LocalProxy, create_environ, SharedDataMiddleware, \
     ImmutableDict, cached_property, wrap_file, Headers, \
     import_string
from werkzeug.routing import Map, Rule
from werkzeug.exceptions import HTTPException, InternalServerError
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

# a lock used for logger initialization
_logger_lock = Lock()


class Request(RequestBase):
    """The request object used by default in flask.  Remembers the
    matched endpoint and view arguments.

    It is what ends up as :class:`~flask.request`.  If you want to replace
    the request object used you can subclass this and set
    :attr:`~flask.Flask.request_class` to your subclass.
    """

    #: the endpoint that matched the request.  This in combination with
    #: :attr:`view_args` can be used to reconstruct the same or a
    #: modified URL.  If an exception happened when matching, this will
    #: be `None`.
    endpoint = None

    #: a dict of view arguments that matched the request.  If an exception
    #: happened when matching, this will be `None`.
    view_args = None

    #: if matching the URL failed, this is the exception that will be
    #: raised / was raised as part of the request handling.  This is
    #: usually a :exc:`~werkzeug.exceptions.NotFound` exception or
    #: something similar.
    routing_exception = None

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
    set :attr:`~flask.Flask.response_class` to your subclass.
    """
    default_mimetype = 'text/html'


class _RequestGlobals(object):
    pass


class Session(SecureCookie):
    """Expands the session with support for switching between permanent
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
        self.url_adapter = app.url_map.bind_to_environ(environ,
            server_name=app.config['SERVER_NAME'])
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

    def push(self):
        """Binds the request context."""
        _request_ctx_stack.push(self)

    def pop(self):
        """Pops the request context."""
        _request_ctx_stack.pop()

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        # do not pop the request stack if we are in debug mode and an
        # exception happened.  This will allow the debugger to still
        # access the request object in the interactive shell.  Furthermore
        # the context can be force kept alive for the test client.
        if not self.request.environ.get('flask._preserve_context') and \
           (tb is None or not self.app.debug):
            self.pop()


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
    template named `_cider.html` with the following contents:

    .. sourcecode:: html+jinja

       {% macro hello(name) %}Hello {{ name }}!{% endmacro %}

    You can access this from Python code like this::

        hello = get_template_attribute('_cider.html', 'hello')
        return hello('World')

    .. versionadded:: 0.2

    :param template_name: the name of the template
    :param attribute: the name of the variable of macro to acccess
    """
    return getattr(current_app.jinja_env.get_template(template_name).module,
                   attribute)


def flash(message, category='message'):
    """Flashes a message to the next request.  In order to remove the
    flashed message from the session and to display it to the user,
    the template has to call :func:`get_flashed_messages`.

    .. versionchanged: 0.3
       `category` parameter added.

    :param message: the message to be flashed.
    :param category: the category for the message.  The following values
                     are recommended: ``'message'`` for any kind of message,
                     ``'error'`` for errors, ``'info'`` for information
                     messages and ``'warning'`` for warnings.  However any
                     kind of string can be used as category.
    """
    session.setdefault('_flashes', []).append((category, message))


def get_flashed_messages(with_categories=False):
    """Pulls all flashed messages from the session and returns them.
    Further calls in the same request to the function will return
    the same messages.  By default just the messages are returned,
    but when `with_categories` is set to `True`, the return value will
    be a list of tuples in the form ``(category, message)`` instead.

    Example usage:

    .. sourcecode:: html+jinja

        {% for category, msg in get_flashed_messages(with_categories=true) %}
          <p class=flash-{{ category }}>{{ msg }}
        {% endfor %}

    .. versionchanged:: 0.3
       `with_categories` parameter added.

    :param with_categories: set to `True` to also receive categories.
    """
    flashes = _request_ctx_stack.top.flashes
    if flashes is None:
        _request_ctx_stack.top.flashes = flashes = session.pop('_flashes', [])
    if not with_categories:
        return [x[1] for x in flashes]
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

    This requires Python 2.6 or an installed version of simplejson.  For
    security reasons only objects are supported toplevel.  For more
    information about this, have a look at :ref:`json-security`.

    .. versionadded:: 0.2
    """
    if __debug__:
        _assert_have_json()
    return current_app.response_class(json.dumps(dict(*args, **kwargs),
        indent=None if request.is_xhr else 2), mimetype='application/json')


def send_file(filename_or_fp, mimetype=None, as_attachment=False,
              attachment_filename=None):
    """Sends the contents of a file to the client.  This will use the
    most efficient method available and configured.  By default it will
    try to use the WSGI server's file_wrapper support.  Alternatively
    you can set the application's :attr:`~Flask.use_x_sendfile` attribute
    to ``True`` to directly emit an `X-Sendfile` header.  This however
    requires support of the underlying webserver for `X-Sendfile`.

    By default it will try to guess the mimetype for you, but you can
    also explicitly provide one.  For extra security you probably want
    to sent certain files as attachment (HTML for instance).

    Please never pass filenames to this function from user sources without
    checking them first.  Something like this is usually sufficient to
    avoid security problems::

        if '..' in filename or filename.startswith('/'):
            abort(404)

    .. versionadded:: 0.2

    :param filename_or_fp: the filename of the file to send.  This is
                           relative to the :attr:`~Flask.root_path` if a
                           relative path is specified.
                           Alternatively a file object might be provided
                           in which case `X-Sendfile` might not work and
                           fall back to the traditional method.
    :param mimetype: the mimetype of the file if provided, otherwise
                     auto detection happens.
    :param as_attachment: set to `True` if you want to send this file with
                          a ``Content-Disposition: attachment`` header.
    :param attachment_filename: the filename for the attachment if it
                                differs from the file's filename.
    """
    if isinstance(filename_or_fp, basestring):
        filename = filename_or_fp
        file = None
    else:
        file = filename_or_fp
        filename = getattr(file, 'name', None)
    if filename is not None:
        filename = os.path.join(current_app.root_path, filename)
    if mimetype is None and (filename or attachment_filename):
        mimetype = mimetypes.guess_type(filename or attachment_filename)[0]
    if mimetype is None:
        mimetype = 'application/octet-stream'

    headers = Headers()
    if as_attachment:
        if attachment_filename is None:
            if filename is None:
                raise TypeError('filename unavailable, required for '
                                'sending as attachment')
            attachment_filename = os.path.basename(filename)
        headers.add('Content-Disposition', 'attachment',
                    filename=attachment_filename)

    if current_app.use_x_sendfile and filename:
        if file is not None:
            file.close()
        headers['X-Sendfile'] = filename
        data = None
    else:
        if file is None:
            file = open(filename, 'rb')
        data = wrap_file(request.environ, file)

    return Response(data, mimetype=mimetype, headers=headers,
                    direct_passthrough=True)


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
        #: The name of the package or module.  Do not change this once
        #: it was set by the constructor.
        self.import_name = import_name

        #: Where is the app root located?
        self.root_path = _get_package_path(self.import_name)

    def open_resource(self, resource):
        """Opens a resource from the application's resource folder.  To see
        how this works, consider the following folder structure::

            /myapplication.py
            /schemal.sql
            /static
                /style.css
            /templates
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
            if state.url_prefix:
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
        before each request, even if outside of a module.
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
        is executed after each request, even if outside of the module.
        """
        self._record(lambda s: s.app.after_request_funcs
            .setdefault(None, []).append(f))
        return f

    def context_processor(self, f):
        """Like :meth:`Flask.context_processor` but for a module.  This
        function is only executed for requests handled by a module.
        """
        self._record(lambda s: s.app.template_context_processors
            .setdefault(self.name, []).append(f))
        return f

    def app_context_processor(self, f):
        """Like :meth:`Flask.context_processor` but for a module.  Such a
        function is executed each request, even if outside of the module.
        """
        self._record(lambda s: s.app.template_context_processors
            .setdefault(None, []).append(f))
        return f

    def app_errorhandler(self, code):
        """Like :meth:`Flask.errorhandler` but for a module.  This
        handler is used for all requests, even if outside of the module.

        .. versionadded:: 0.4
        """
        def decorator(f):
            self._record(lambda s: s.app.errorhandler(code)(f))
            return f
        return decorator

    def _record(self, func):
        self._register_events.append(func)


class ConfigAttribute(object):
    """Makes an attribute forward to the config"""

    def __init__(self, name):
        self.__name__ = name

    def __get__(self, obj, type=None):
        if obj is None:
            return self
        return obj.config[self.__name__]

    def __set__(self, obj, value):
        obj.config[self.__name__] = value


class Config(dict):
    """Works exactly like a dict but provides ways to fill it from files
    or special dictionaries.  There are two common patterns to populate the
    config.

    Either you can fill the config from a config file::

        app.config.from_pyfile('yourconfig.cfg')

    Or alternatively you can define the configuration options in the
    module that calls :meth:`from_object` or provide an import path to
    a module that should be loaded.  It is also possible to tell it to
    use the same module and with that provide the configuration values
    just before the call::

        DEBUG = True
        SECRET_KEY = 'development key'
        app.config.from_object(__name__)

    In both cases (loading from any Python file or loading from modules),
    only uppercase keys are added to the config.  This makes it possible to use
    lowercase values in the config file for temporary values that are not added
    to the config or to define the config keys in the same file that implements
    the application.

    Probably the most interesting way to load configurations is from an
    environment variable pointing to a file::

        app.config.from_envvar('YOURAPPLICATION_SETTINGS')

    In this case before launching the application you have to set this
    environment variable to the file you want to use.  On Linux and OS X
    use the export statement::

        export YOURAPPLICATION_SETTINGS='/path/to/config/file'

    On windows use `set` instead.

    :param root_path: path to which files are read relative from.  When the
                      config object is created by the application, this is
                      the application's :attr:`~flask.Flask.root_path`.
    :param defaults: an optional dictionary of default values
    """

    def __init__(self, root_path, defaults=None):
        dict.__init__(self, defaults or {})
        self.root_path = root_path

    def from_envvar(self, variable_name, silent=False):
        """Loads a configuration from an environment variable pointing to
        a configuration file.  This basically is just a shortcut with nicer
        error messages for this line of code::

            app.config.from_pyfile(os.environ['YOURAPPLICATION_SETTINGS'])

        :param variable_name: name of the environment variable
        :param silent: set to `True` if you want silent failing for missing
                       files.
        :return: bool. `True` if able to load config, `False` otherwise.
        """
        rv = os.environ.get(variable_name)
        if not rv:
            if silent:
                return False
            raise RuntimeError('The environment variable %r is not set '
                               'and as such configuration could not be '
                               'loaded.  Set this variable and make it '
                               'point to a configuration file' %
                               variable_name)
        self.from_pyfile(rv)
        return True

    def from_pyfile(self, filename):
        """Updates the values in the config from a Python file.  This function
        behaves as if the file was imported as module with the
        :meth:`from_object` function.

        :param filename: the filename of the config.  This can either be an
                         absolute filename or a filename relative to the
                         root path.
        """
        filename = os.path.join(self.root_path, filename)
        d = type(sys)('config')
        d.__file__ = filename
        execfile(filename, d.__dict__)
        self.from_object(d)

    def from_object(self, obj):
        """Updates the values from the given object.  An object can be of one
        of the following two types:

        -   a string: in this case the object with that name will be imported
        -   an actual object reference: that object is used directly

        Objects are usually either modules or classes.

        Just the uppercase variables in that object are stored in the config
        after lowercasing.  Example usage::

            app.config.from_object('yourapplication.default_config')
            from yourapplication import default_config
            app.config.from_object(default_config)

        You should not use this function to load the actual configuration but
        rather configuration defaults.  The actual config should be loaded
        with :meth:`from_pyfile` and ideally from a location not within the
        package because the package might be installed system wide.

        :param obj: an import name or object
        """
        if isinstance(obj, basestring):
            obj = import_string(obj)
        for key in dir(obj):
            if key.isupper():
                self[key] = getattr(obj, key)

    def __repr__(self):
        return '<%s %s>' % (self.__class__.__name__, dict.__repr__(self))


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
    """

    #: The class that is used for request objects.  See :class:`~flask.Request`
    #: for more information.
    request_class = Request

    #: The class that is used for response objects.  See
    #: :class:`~flask.Response` for more information.
    response_class = Response

    #: Path for the static files.  If you don't want to use static files
    #: you can set this value to `None` in which case no URL rule is added
    #: and the development server will no longer serve any static files.
    static_path = '/static'

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
        autoescape=True,
        extensions=['jinja2.ext.autoescape', 'jinja2.ext.with_']
    )

    #: Default configuration parameters.
    default_config = ImmutableDict({
        'DEBUG':                                False,
        'TESTING':                              False,
        'SECRET_KEY':                           None,
        'SESSION_COOKIE_NAME':                  'session',
        'PERMANENT_SESSION_LIFETIME':           timedelta(days=31),
        'USE_X_SENDFILE':                       False,
        'LOGGER_NAME':                          None,
        'SERVER_NAME':                          None
    })

    def __init__(self, import_name):
        _PackageBoundObject.__init__(self, import_name)

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
        #: to register a view function, use the :meth:`route` decorator.
        self.view_functions = {}

        #: A dictionary of all registered error handlers.  The key is
        #: be the error code as integer, the value the function that
        #: should handle that error.
        #: To register a error handler, use the :meth:`errorhandler`
        #: decorator.
        self.error_handlers = {}

        #: A dictionary with lists of functions that should be called at the
        #: beginning of the request.  The key of the dictionary is the name of
        #: the module this function is active for, `None` for all requests.
        #: This can for example be used to open database connections or
        #: getting hold of the currently logged in user.  To register a
        #: function here, use the :meth:`before_request` decorator.
        self.before_request_funcs = {}

        #: A dictionary with lists of functions that should be called after
        #: each request.  The key of the dictionary is the name of the module
        #: this function is active for, `None` for all requests.  This can for
        #: example be used to open database connections or getting hold of the
        #: currently logged in user.  To register a function here, use the
        #: :meth:`before_request` decorator.
        self.after_request_funcs = {}

        #: A dictionary with list of functions that are called without argument
        #: to populate the template context.  They key of the dictionary is the
        #: name of the module this function is active for, `None` for all
        #: requests.  Each returns a dictionary that the template context is
        #: updated with.  To register a function here, use the
        #: :meth:`context_processor` decorator.
        self.template_context_processors = {
            None: [_default_template_ctx_processor]
        }

        #: The :class:`~werkzeug.routing.Map` for this instance.  You can use
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

        #: The Jinja2 environment.  It is created from the
        #: :attr:`jinja_options` and the loader that is returned
        #: by the :meth:`create_jinja_loader` function.
        self.jinja_env = Environment(loader=self.create_jinja_loader(),
                                     **self.jinja_options)
        self.jinja_env.globals.update(
            url_for=url_for,
            get_flashed_messages=get_flashed_messages
        )
        self.jinja_env.filters['tojson'] = _tojson_filter

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
            from logging import getLogger, StreamHandler, Formatter, \
                                Logger,  DEBUG
            class DebugLogger(Logger):
                def getEffectiveLevel(x):
                    return DEBUG if self.debug else Logger.getEffectiveLevel(x)
            class DebugHandler(StreamHandler):
                def emit(x, record):
                    StreamHandler.emit(x, record) if self.debug else None
            handler = DebugHandler()
            handler.setLevel(DEBUG)
            handler.setFormatter(Formatter(self.debug_log_format))
            logger = getLogger(self.logger_name)
            logger.__class__ = DebugLogger
            logger.addHandler(handler)
            self._logger = logger
            return logger

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

        .. admonition:: Keep in Mind

           Flask will supress any server error with a generic error page
           unless it is in debug mode.  As such to enable just the
           interactive debugger without the code reloading, you ahve to
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

    def test_client(self):
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
        """
        from werkzeug import Client
        class FlaskClient(Client):
            preserve_context = context_preserved = False
            def open(self, *args, **kwargs):
                if self.context_preserved:
                    _request_ctx_stack.pop()
                    self.context_preserved = False
                kwargs.setdefault('environ_overrides', {}) \
                    ['flask._preserve_context'] = self.preserve_context
                old = _request_ctx_stack.top
                try:
                    return Client.open(self, *args, **kwargs)
                finally:
                    self.context_preserved = _request_ctx_stack.top is not old
            def __enter__(self):
                self.preserve_context = True
                return self
            def __exit__(self, exc_type, exc_value, tb):
                self.preserve_context = False
                if self.context_preserved:
                    _request_ctx_stack.pop()
        return FlaskClient(self, self.response_class, use_cookies=True)

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
            def page_not_found(error):
                return 'This page does not exist', 404

        You can also register a function as error handler without using
        the :meth:`errorhandler` decorator.  The following example is
        equivalent to the one above::

            def page_not_found(error):
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

    def handle_http_exception(self, e):
        """Handles an HTTP exception.  By default this will invoke the
        registered error handlers and fall back to returning the
        exception as response.

        .. versionadded: 0.3
        """
        handler = self.error_handlers.get(e.code)
        if handler is None:
            return e
        return handler(e)

    def handle_exception(self, e):
        """Default exception handling that kicks in when an exception
        occours that is not catched.  In debug mode the exception will
        be re-raised immediately, otherwise it is logged and the handler
        for a 500 internal server error is used.  If no such handler
        exists, a default 500 internal server error message is displayed.

        .. versionadded: 0.3
        """
        handler = self.error_handlers.get(500)
        if self.debug:
            raise
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
        """
        req = _request_ctx_stack.top.request
        try:
            if req.routing_exception is not None:
                raise req.routing_exception
            return self.view_functions[req.endpoint](**req.view_args)
        except HTTPException, e:
            return self.handle_http_exception(e)

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

        .. versionchanged:: 0.4
           The :meth:`after_request` functions are now called even if an
           error handler took over request processing.  This ensures that
           even if an exception happens database have the chance to
           properly close the connection.

        :param environ: a WSGI environment
        :param start_response: a callable accepting a status code,
                               a list of headers and an optional
                               exception context to start the response
        """
        with self.request_context(environ):
            try:
                rv = self.preprocess_request()
                if rv is None:
                    rv = self.dispatch_request()
                response = self.make_response(rv)
            except Exception, e:
                response = self.make_response(self.handle_exception(e))
            try:
                response = self.process_response(response)
            except Exception, e:
                response = self.make_response(self.handle_exception(e))
            return response(environ, start_response)

    def request_context(self, environ):
        """Creates a request context from the given environment and binds
        it to the current context.  This must be used in combination with
        the `with` statement because the request is only bound to the
        current context for the duration of the `with` block.

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

        The big advantage of this approach is that you can use it without
        the try/finally statement in a shell for interactive testing:

        >>> ctx = app.test_request_context()
        >>> ctx.bind()
        >>> request.path
        u'/'
        >>> ctx.unbind()

        .. versionchanged:: 0.3
           Added support for non-with statement usage and `with` statement
           is now passed the ctx object.

        :param environ: a WSGI environment
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
