from functools import update_wrapper

from werkzeug.exceptions import default_exceptions
from werkzeug.exceptions import HTTPException

from .helpers import _PackageBoundObject
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
                "A setup function was called after the "
                "first request was handled.  This usually indicates a bug "
                "in the application where a module was not imported "
                "and decorators or other functionality was called too late.\n"
                "To fix this make sure to import all your view modules, "
                "database models and everything related at a central place "
                "before the application starts serving requests."
            )
        return f(self, *args, **kwargs)

    return update_wrapper(wrapper_func, f)


class Scaffold(_PackageBoundObject):
    """A common base for class Flask and class Blueprint.
    """

    #: Skeleton local JSON decoder class to use.
    #: Set to ``None`` to use the app's :class:`~flask.app.Flask.json_encoder`.
    json_encoder = None

    #: Skeleton local JSON decoder class to use.
    #: Set to ``None`` to use the app's :class:`~flask.app.Flask.json_decoder`.
    json_decoder = None

    #: The name of the package or module that this app belongs to. Do not
    #: change this once it is set by the constructor.
    import_name = None

    #: Location of the template files to be added to the template lookup.
    #: ``None`` if templates should not be added.
    template_folder = None

    #: Absolute path to the package on the filesystem. Used to look up
    #: resources contained in the package.
    root_path = None

    def __init__(
        self,
        import_name,
        static_folder="static",
        static_url_path=None,
        template_folder=None,
        root_path=None,
    ):
        super().__init__(
            import_name=import_name,
            template_folder=template_folder,
            root_path=root_path,
        )
        self.static_folder = static_folder
        self.static_url_path = static_url_path

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
        self.error_handler_spec = {}

        #: A dictionary with lists of functions that will be called at the
        #: beginning of each request. The key of the dictionary is the name of
        #: the blueprint this function is active for, or ``None`` for all
        #: requests. To register a function, use the :meth:`before_request`
        #: decorator.
        self.before_request_funcs = {}

        #: A dictionary with lists of functions that should be called after
        #: each request.  The key of the dictionary is the name of the blueprint
        #: this function is active for, ``None`` for all requests.  This can for
        #: example be used to close database connections. To register a function
        #: here, use the :meth:`after_request` decorator.
        self.after_request_funcs = {}

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
        self.teardown_request_funcs = {}

        #: A dictionary with list of functions that are called without argument
        #: to populate the template context.  The key of the dictionary is the
        #: name of the blueprint this function is active for, ``None`` for all
        #: requests.  Each returns a dictionary that the template context is
        #: updated with.  To register a function here, use the
        #: :meth:`context_processor` decorator.
        self.template_context_processors = {None: [_default_template_ctx_processor]}

        #: A dictionary with lists of functions that are called before the
        #: :attr:`before_request_funcs` functions. The key of the dictionary is
        #: the name of the blueprint this function is active for, or ``None``
        #: for all requests. To register a function, use
        #: :meth:`url_value_preprocessor`.
        #:
        #: .. versionadded:: 0.7
        self.url_value_preprocessors = {}

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
        self.url_default_functions = {}

    def _is_setup_finished(self):
        raise NotImplementedError

    def route(self, rule, **options):
        """A decorator that is used to register a view function for a
        given URL rule.  This does the same thing as :meth:`add_url_rule`
        but is intended for decorator usage::

            @app.route('/')
            def index():
                return 'Hello World'

        For more information refer to :ref:`url-route-registrations`.

        :param rule: the URL rule as string
        :param endpoint: the endpoint for the registered URL rule.  Flask
                         itself assumes the name of the view function as
                         endpoint
        :param options: the options to be forwarded to the underlying
                        :class:`~werkzeug.routing.Rule` object.  A change
                        to Werkzeug is handling of method options.  methods
                        is a list of methods this rule should be limited
                        to (``GET``, ``POST`` etc.).  By default a rule
                        just listens for ``GET`` (and implicitly ``HEAD``).
                        Starting with Flask 0.6, ``OPTIONS`` is implicitly
                        added and handled by the standard request handling.
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
        self.before_request_funcs.setdefault(None, []).append(f)
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
        self.after_request_funcs.setdefault(None, []).append(f)
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
        self.teardown_request_funcs.setdefault(None, []).append(f)
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
        self.url_value_preprocessors.setdefault(None, []).append(f)
        return f

    @setupmethod
    def url_defaults(self, f):
        """Callback function for URL defaults for all view functions of the
        application.  It's called with the endpoint and values and should
        update the values passed in place.
        """
        self.url_default_functions.setdefault(None, []).append(f)
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

        handlers = self.error_handler_spec.setdefault(key, {}).setdefault(code, {})
        handlers[exc_class] = f

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
