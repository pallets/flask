import os
import pkgutil
import sys
from collections import defaultdict
from functools import update_wrapper

from jinja2 import FileSystemLoader
from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException

from .cli import AppGroup
from .globals import current_app
from .helpers import locked_cached_property
from .helpers import send_from_directory
from .templating import _default_template_ctx_processor

# a singleton sentinel value for parameter defaults
_sentinel = object()


def setupmethod(f):
    """Wraps a method so that it performs a check in debug mode if the
    first request was already handled.
    """

    def wrapper_func(self, *args, **kwargs):
        if self._is_setup_finished():
            raise AssertionError(
                "A setup function was called after the first request "
                "was handled. This usually indicates a bug in the"
                " application where a module was not imported and"
                " decorators or other functionality was called too"
                " late.\nTo fix this make sure to import all your view"
                " modules, database models, and everything related at a"
                " central place before the application starts serving"
                " requests."
            )
        return f(self, *args, **kwargs)

    return update_wrapper(wrapper_func, f)


class Scaffold:
    """A common base for :class:`~flask.app.Flask` and
    :class:`~flask.blueprints.Blueprint`.
    """

    name: str
    _static_folder = None
    _static_url_path = None

    #: Skeleton local JSON decoder class to use.
    #: Set to ``None`` to use the app's :class:`~flask.app.Flask.json_encoder`.
    json_encoder = None

    #: Skeleton local JSON decoder class to use.
    #: Set to ``None`` to use the app's :class:`~flask.app.Flask.json_decoder`.
    json_decoder = None

    def __init__(
        self,
        import_name,
        static_folder="static",
        static_url_path=None,
        template_folder=None,
        root_path=None,
    ):
        #: The name of the package or module that this object belongs
        #: to. Do not change this once it is set by the constructor.
        self.import_name = import_name

        self.static_folder = static_folder
        self.static_url_path = static_url_path

        #: The path to the templates folder, relative to
        #: :attr:`root_path`, to add to the template loader. ``None`` if
        #: templates should not be added.
        self.template_folder = template_folder

        if root_path is None:
            root_path = get_root_path(self.import_name)

        #: Absolute path to the package on the filesystem. Used to look
        #: up resources contained in the package.
        self.root_path = root_path

        #: The Click command group for registering CLI commands for this
        #: object. The commands are available from the ``flask`` command
        #: once the application has been discovered and blueprints have
        #: been registered.
        self.cli = AppGroup()

        #: A dictionary of all view functions registered.  The keys will
        #: be function names which are also used to generate URLs and
        #: the values are the function objects themselves.
        #: To register a view function, use the :meth:`route` decorator.
        self.view_functions = {}

        #: A dictionary of all registered error handlers.  The key is ``None``
        #: for error handlers active on the application, otherwise the key is
        #: the name of the blueprint.  Each key points to another dictionary
        #: where the key is the status code of the http exception.  The
        #: special key ``None`` points to a list of tuples where the first item
        #: is the class for the instance check and the second the error handler
        #: function.
        #:
        #: To register an error handler, use the :meth:`errorhandler`
        #: decorator.
        self.error_handler_spec = defaultdict(lambda: defaultdict(dict))

        #: A dictionary with lists of functions that will be called at the
        #: beginning of each request. The key of the dictionary is the name of
        #: the blueprint this function is active for, or ``None`` for all
        #: requests. To register a function, use the :meth:`before_request`
        #: decorator.
        self.before_request_funcs = defaultdict(list)

        #: A dictionary with lists of functions that should be called after
        #: each request.  The key of the dictionary is the name of the blueprint
        #: this function is active for, ``None`` for all requests.  This can for
        #: example be used to close database connections. To register a function
        #: here, use the :meth:`after_request` decorator.
        self.after_request_funcs = defaultdict(list)

        #: A dictionary with lists of functions that are called after
        #: each request, even if an exception has occurred. The key of the
        #: dictionary is the name of the blueprint this function is active for,
        #: ``None`` for all requests. These functions are not allowed to modify
        #: the request, and their return values are ignored. If an exception
        #: occurred while processing the request, it gets passed to each
        #: teardown_request function. To register a function here, use the
        #: :meth:`teardown_request` decorator.
        #:
        #: .. versionadded:: 0.7
        self.teardown_request_funcs = defaultdict(list)

        #: A dictionary with list of functions that are called without argument
        #: to populate the template context.  The key of the dictionary is the
        #: name of the blueprint this function is active for, ``None`` for all
        #: requests.  Each returns a dictionary that the template context is
        #: updated with.  To register a function here, use the
        #: :meth:`context_processor` decorator.
        self.template_context_processors = defaultdict(
            list, {None: [_default_template_ctx_processor]}
        )

        #: A dictionary with lists of functions that are called before the
        #: :attr:`before_request_funcs` functions. The key of the dictionary is
        #: the name of the blueprint this function is active for, or ``None``
        #: for all requests. To register a function, use
        #: :meth:`url_value_preprocessor`.
        #:
        #: .. versionadded:: 0.7
        self.url_value_preprocessors = defaultdict(list)

        #: A dictionary with lists of functions that can be used as URL value
        #: preprocessors.  The key ``None`` here is used for application wide
        #: callbacks, otherwise the key is the name of the blueprint.
        #: Each of these functions has the chance to modify the dictionary
        #: of URL values before they are used as the keyword arguments of the
        #: view function.  For each function registered this one should also
        #: provide a :meth:`url_defaults` function that adds the parameters
        #: automatically again that were removed that way.
        #:
        #: .. versionadded:: 0.7
        self.url_default_functions = defaultdict(list)

    def __repr__(self):
        return f"<{type(self).__name__} {self.name!r}>"

    def _is_setup_finished(self):
        raise NotImplementedError

    @property
    def static_folder(self):
        """The absolute path to the configured static folder. ``None``
        if no static folder is set.
        """
        if self._static_folder is not None:
            return os.path.join(self.root_path, self._static_folder)

    @static_folder.setter
    def static_folder(self, value):
        if value is not None:
            value = os.fspath(value).rstrip(r"\/")

        self._static_folder = value

    @property
    def has_static_folder(self):
        """``True`` if :attr:`static_folder` is set.

        .. versionadded:: 0.5
        """
        return self.static_folder is not None

    @property
    def static_url_path(self):
        """The URL prefix that the static route will be accessible from.

        If it was not configured during init, it is derived from
        :attr:`static_folder`.
        """
        if self._static_url_path is not None:
            return self._static_url_path

        if self.static_folder is not None:
            basename = os.path.basename(self.static_folder)
            return f"/{basename}".rstrip("/")

    @static_url_path.setter
    def static_url_path(self, value):
        if value is not None:
            value = value.rstrip("/")

        self._static_url_path = value

    def get_send_file_max_age(self, filename):
        """Used by :func:`send_file` to determine the ``max_age`` cache
        value for a given file path if it wasn't passed.

        By default, this returns :data:`SEND_FILE_MAX_AGE_DEFAULT` from
        the configuration of :data:`~flask.current_app`. This defaults
        to ``None``, which tells the browser to use conditional requests
        instead of a timed cache, which is usually preferable.

        .. versionchanged:: 2.0
            The default configuration is ``None`` instead of 12 hours.

        .. versionadded:: 0.9
        """
        value = current_app.send_file_max_age_default

        if value is None:
            return None

        return int(value.total_seconds())

    def send_static_file(self, filename):
        """The view function used to serve files from
        :attr:`static_folder`. A route is automatically registered for
        this view at :attr:`static_url_path` if :attr:`static_folder` is
        set.

        .. versionadded:: 0.5
        """
        if not self.has_static_folder:
            raise RuntimeError("'static_folder' must be set to serve static_files.")

        # send_file only knows to call get_send_file_max_age on the app,
        # call it here so it works for blueprints too.
        max_age = self.get_send_file_max_age(filename)
        return send_from_directory(self.static_folder, filename, max_age=max_age)

    @locked_cached_property
    def jinja_loader(self):
        """The Jinja loader for this object's templates. By default this
        is a class :class:`jinja2.loaders.FileSystemLoader` to
        :attr:`template_folder` if it is set.

        .. versionadded:: 0.5
        """
        if self.template_folder is not None:
            return FileSystemLoader(os.path.join(self.root_path, self.template_folder))

    def open_resource(self, resource, mode="rb"):
        """Open a resource file relative to :attr:`root_path` for
        reading.

        For example, if the file ``schema.sql`` is next to the file
        ``app.py`` where the ``Flask`` app is defined, it can be opened
        with:

        .. code-block:: python

            with app.open_resource("schema.sql") as f:
                conn.executescript(f.read())

        :param resource: Path to the resource relative to
            :attr:`root_path`.
        :param mode: Open the file in this mode. Only reading is
            supported, valid values are "r" (or "rt") and "rb".
        """
        if mode not in {"r", "rt", "rb"}:
            raise ValueError("Resources can only be opened for reading.")

        return open(os.path.join(self.root_path, resource), mode)

    def _method_route(self, method, rule, options):
        if "methods" in options:
            raise TypeError("Use the 'route' decorator to use the 'methods' argument.")

        return self.route(rule, methods=[method], **options)

    def get(self, rule, **options):
        """Shortcut for :meth:`route` with ``methods=["GET"]``.

        .. versionadded:: 2.0
        """
        return self._method_route("GET", rule, options)

    def post(self, rule, **options):
        """Shortcut for :meth:`route` with ``methods=["POST"]``.

        .. versionadded:: 2.0
        """
        return self._method_route("POST", rule, options)

    def put(self, rule, **options):
        """Shortcut for :meth:`route` with ``methods=["PUT"]``.

        .. versionadded:: 2.0
        """
        return self._method_route("PUT", rule, options)

    def delete(self, rule, **options):
        """Shortcut for :meth:`route` with ``methods=["DELETE"]``.

        .. versionadded:: 2.0
        """
        return self._method_route("DELETE", rule, options)

    def patch(self, rule, **options):
        """Shortcut for :meth:`route` with ``methods=["PATCH"]``.

        .. versionadded:: 2.0
        """
        return self._method_route("PATCH", rule, options)

    def route(self, rule, **options):
        """A decorator that is used to register a view function for a
        given URL rule. This does the same thing as :meth:`add_url_rule`
        but is used as a decorator. See :meth:`add_url_rule` and
        :ref:`url-route-registrations` for more information.

        .. code-block:: python

            @app.route("/")
            def index():
                return "Hello World"

        :param rule: The URL rule as a string.
        :param options: The options to be forwarded to the underlying
            :class:`~werkzeug.routing.Rule` object.
        """

        def decorator(f):
            endpoint = options.pop("endpoint", None)
            self.add_url_rule(rule, endpoint, f, **options)
            return f

        return decorator

    @setupmethod
    def add_url_rule(
        self,
        rule,
        endpoint=None,
        view_func=None,
        provide_automatic_options=None,
        **options,
    ):
        raise NotImplementedError

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

    @setupmethod
    def before_request(self, f):
        """Registers a function to run before each request.

        For example, this can be used to open a database connection, or to load
        the logged in user from the session.

        The function will be called without any arguments. If it returns a
        non-None value, the value is handled as if it was the return value from
        the view, and further request handling is stopped.
        """
        self.before_request_funcs[None].append(f)
        return f

    @setupmethod
    def after_request(self, f):
        """Register a function to be run after each request.

        Your function must take one parameter, an instance of
        :attr:`response_class` and return a new response object or the
        same (see :meth:`process_response`).

        As of Flask 0.7 this function might not be executed at the end of the
        request in case an unhandled exception occurred.
        """
        self.after_request_funcs[None].append(f)
        return f

    @setupmethod
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

        Generally teardown functions must take every necessary step to avoid
        that they will fail.  If they do execute code that might fail they
        will have to surround the execution of these code by try/except
        statements and log occurring errors.

        When a teardown function was called because of an exception it will
        be passed an error object.

        The return values of teardown functions are ignored.

        .. admonition:: Debug Note

           In debug mode Flask will not tear down a request on an exception
           immediately.  Instead it will keep it alive so that the interactive
           debugger can still access it.  This behavior can be controlled
           by the ``PRESERVE_CONTEXT_ON_EXCEPTION`` configuration variable.
        """
        self.teardown_request_funcs[None].append(f)
        return f

    @setupmethod
    def context_processor(self, f):
        """Registers a template context processor function."""
        self.template_context_processors[None].append(f)
        return f

    @setupmethod
    def url_value_preprocessor(self, f):
        """Register a URL value preprocessor function for all view
        functions in the application. These functions will be called before the
        :meth:`before_request` functions.

        The function can modify the values captured from the matched url before
        they are passed to the view. For example, this can be used to pop a
        common language code value and place it in ``g`` rather than pass it to
        every view.

        The function is passed the endpoint name and values dict. The return
        value is ignored.
        """
        self.url_value_preprocessors[None].append(f)
        return f

    @setupmethod
    def url_defaults(self, f):
        """Callback function for URL defaults for all view functions of the
        application.  It's called with the endpoint and values and should
        update the values passed in place.
        """
        self.url_default_functions[None].append(f)
        return f

    @setupmethod
    def errorhandler(self, code_or_exception):
        """Register a function to handle errors by code or exception class.

        A decorator that is used to register a function given an
        error code.  Example::

            @app.errorhandler(404)
            def page_not_found(error):
                return 'This page does not exist', 404

        You can also register handlers for arbitrary exceptions::

            @app.errorhandler(DatabaseError)
            def special_exception_handler(error):
                return 'Database connection failed', 500

        .. versionadded:: 0.7
            Use :meth:`register_error_handler` instead of modifying
            :attr:`error_handler_spec` directly, for application wide error
            handlers.

        .. versionadded:: 0.7
           One can now additionally also register custom exception types
           that do not necessarily have to be a subclass of the
           :class:`~werkzeug.exceptions.HTTPException` class.

        :param code_or_exception: the code as integer for the handler, or
                                  an arbitrary exception
        """

        def decorator(f):
            self._register_error_handler(None, code_or_exception, f)
            return f

        return decorator

    @setupmethod
    def register_error_handler(self, code_or_exception, f):
        """Alternative error attach function to the :meth:`errorhandler`
        decorator that is more straightforward to use for non decorator
        usage.

        .. versionadded:: 0.7
        """
        self._register_error_handler(None, code_or_exception, f)

    @setupmethod
    def _register_error_handler(self, key, code_or_exception, f):
        """
        :type key: None|str
        :type code_or_exception: int|T<=Exception
        :type f: callable
        """
        if isinstance(code_or_exception, HTTPException):  # old broken behavior
            raise ValueError(
                "Tried to register a handler for an exception instance"
                f" {code_or_exception!r}. Handlers can only be"
                " registered for exception classes or HTTP error codes."
            )

        try:
            exc_class, code = self._get_exc_class_and_code(code_or_exception)
        except KeyError:
            raise KeyError(
                f"'{code_or_exception}' is not a recognized HTTP error"
                " code. Use a subclass of HTTPException with that code"
                " instead."
            )

        self.error_handler_spec[key][code][exc_class] = f

    @staticmethod
    def _get_exc_class_and_code(exc_class_or_code):
        """Get the exception class being handled. For HTTP status codes
        or ``HTTPException`` subclasses, return both the exception and
        status code.

        :param exc_class_or_code: Any exception class, or an HTTP status
            code as an integer.
        """
        if isinstance(exc_class_or_code, int):
            exc_class = default_exceptions[exc_class_or_code]
        else:
            exc_class = exc_class_or_code

        assert issubclass(
            exc_class, Exception
        ), "Custom exceptions must be subclasses of Exception."

        if issubclass(exc_class, HTTPException):
            return exc_class, exc_class.code
        else:
            return exc_class, None


def _endpoint_from_view_func(view_func):
    """Internal helper that returns the default endpoint for a given
    function.  This always is the function name.
    """
    assert view_func is not None, "expected view func if endpoint is not provided."
    return view_func.__name__


def get_root_path(import_name):
    """Find the root path of a package, or the path that contains a
    module. If it cannot be found, returns the current working
    directory.

    Not to be confused with the value returned by :func:`find_package`.

    :meta private:
    """
    # Module already imported and has a file attribute. Use that first.
    mod = sys.modules.get(import_name)

    if mod is not None and hasattr(mod, "__file__"):
        return os.path.dirname(os.path.abspath(mod.__file__))

    # Next attempt: check the loader.
    loader = pkgutil.get_loader(import_name)

    # Loader does not exist or we're referring to an unloaded main
    # module or a main module without path (interactive sessions), go
    # with the current working directory.
    if loader is None or import_name == "__main__":
        return os.getcwd()

    if hasattr(loader, "get_filename"):
        filepath = loader.get_filename(import_name)
    else:
        # Fall back to imports.
        __import__(import_name)
        mod = sys.modules[import_name]
        filepath = getattr(mod, "__file__", None)

        # If we don't have a file path it might be because it is a
        # namespace package. In this case pick the root path from the
        # first module that is contained in the package.
        if filepath is None:
            raise RuntimeError(
                "No root path can be found for the provided module"
                f" {import_name!r}. This can happen because the module"
                " came from an import hook that does not provide file"
                " name information or because it's a namespace package."
                " In this case the root path needs to be explicitly"
                " provided."
            )

    # filepath is import_name.py for a module, or __init__.py for a package.
    return os.path.dirname(os.path.abspath(filepath))


def _matching_loader_thinks_module_is_package(loader, mod_name):
    """Attempt to figure out if the given name is a package or a module.

    :param: loader: The loader that handled the name.
    :param mod_name: The name of the package or module.
    """
    # Use loader.is_package if it's available.
    if hasattr(loader, "is_package"):
        return loader.is_package(mod_name)

    cls = type(loader)

    # NamespaceLoader doesn't implement is_package, but all names it
    # loads must be packages.
    if cls.__module__ == "_frozen_importlib" and cls.__name__ == "NamespaceLoader":
        return True

    # Otherwise we need to fail with an error that explains what went
    # wrong.
    raise AttributeError(
        f"'{cls.__name__}.is_package()' must be implemented for PEP 302"
        f" import hooks."
    )


def _find_package_path(root_mod_name):
    """Find the path that contains the package or module."""
    try:
        spec = importlib.util.find_spec(root_mod_name)

        if spec is None:
            raise ValueError("not found")
    # ImportError: the machinery told us it does not exist
    # ValueError:
    #    - the module name was invalid
    #    - the module name is __main__
    #    - *we* raised `ValueError` due to `spec` being `None`
    except (ImportError, ValueError):
        pass  # handled below
    else:
        # namespace package
        if spec.origin in {"namespace", None}:
            return os.path.dirname(next(iter(spec.submodule_search_locations)))
        # a package (with __init__.py)
        elif spec.submodule_search_locations:
            return os.path.dirname(os.path.dirname(spec.origin))
        # just a normal module
        else:
            return os.path.dirname(spec.origin)

    # we were unable to find the `package_path` using PEP 451 loaders
    loader = pkgutil.get_loader(root_mod_name)

    if loader is None or root_mod_name == "__main__":
        # import name is not found, or interactive/main module
        return os.getcwd()

    if hasattr(loader, "get_filename"):
        filename = loader.get_filename(root_mod_name)
    elif hasattr(loader, "archive"):
        # zipimporter's loader.archive points to the .egg or .zip file.
        filename = loader.archive
    else:
        # At least one loader is missing both get_filename and archive:
        # Google App Engine's HardenedModulesHook, use __file__.
        filename = importlib.import_module(root_mod_name).__file__

    package_path = os.path.abspath(os.path.dirname(filename))

    # If the imported name is a package, filename is currently pointing
    # to the root of the package, need to get the current directory.
    if _matching_loader_thinks_module_is_package(loader, root_mod_name):
        package_path = os.path.dirname(package_path)

    return package_path


def find_package(import_name):
    """Find the prefix that a package is installed under, and the path
    that it would be imported from.

    The prefix is the directory containing the standard directory
    hierarchy (lib, bin, etc.). If the package is not installed to the
    system (:attr:`sys.prefix`) or a virtualenv (``site-packages``),
    ``None`` is returned.

    The path is the entry in :attr:`sys.path` that contains the package
    for import. If the package is not installed, it's assumed that the
    package was imported from the current working directory.
    """
    root_mod_name, _, _ = import_name.partition(".")
    package_path = _find_package_path(root_mod_name)
    py_prefix = os.path.abspath(sys.prefix)

    # installed to the system
    if package_path.startswith(py_prefix):
        return py_prefix, package_path

    site_parent, site_folder = os.path.split(package_path)

    # installed to a virtualenv
    if site_folder.lower() == "site-packages":
        parent, folder = os.path.split(site_parent)

        # Windows (prefix/lib/site-packages)
        if folder.lower() == "lib":
            return parent, package_path

        # Unix (prefix/lib/pythonX.Y/site-packages)
        if os.path.basename(parent).lower() == "lib":
            return os.path.dirname(parent), package_path

        # something else (prefix/site-packages)
        return site_parent, package_path

    # not installed
    return None, package_path
