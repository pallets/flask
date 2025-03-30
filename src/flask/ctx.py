from __future__ import annotations

import contextvars
import sys
import typing as t
from functools import update_wrapper
from types import TracebackType
import warnings
from typing import Optional, Union, cast

from werkzeug.exceptions import HTTPException

from . import typing as ft
from .globals import _cv_app
from .globals import _cv_request
from .signals import appcontext_popped
from .signals import appcontext_pushed
from .signals import request_tearing_down

if t.TYPE_CHECKING:  # pragma: no cover
    from _typeshed.wsgi import WSGIEnvironment

    from .app import Flask
    from .sessions import SessionMixin
    from .wrappers import Request


# a singleton sentinel value for parameter defaults
_sentinel = object()

# Context variable for the new unified context
_cv_execution = contextvars.ContextVar[Optional["ExecutionContext"]]("flask.execution_ctx")


class _AppCtxGlobals:
    """A plain object. Used as a namespace for storing data during an
    application context.

    Creating an app context automatically creates this object, which is
    made available as the :data:`g` proxy.

    .. describe:: 'key' in g

        Check whether an attribute is present.

        .. versionadded:: 0.10

    .. describe:: iter(g)

        Return an iterator over the attribute names.

        .. versionadded:: 0.10
    """

    # Define attr methods to let mypy know this is a namespace object
    # that has arbitrary attributes.

    def __getattr__(self, name: str) -> t.Any:
        try:
            return self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def __setattr__(self, name: str, value: t.Any) -> None:
        self.__dict__[name] = value

    def __delattr__(self, name: str) -> None:
        try:
            del self.__dict__[name]
        except KeyError:
            raise AttributeError(name) from None

    def get(self, name: str, default: t.Any | None = None) -> t.Any:
        """Get an attribute by name, or a default value. Like
        :meth:`dict.get`.

        :param name: Name of attribute to get.
        :param default: Value to return if the attribute is not present.

        .. versionadded:: 0.10
        """
        return self.__dict__.get(name, default)

    def pop(self, name: str, default: t.Any = _sentinel) -> t.Any:
        """Get and remove an attribute by name. Like :meth:`dict.pop`.

        :param name: Name of attribute to pop.
        :param default: Value to return if the attribute is not present,
            instead of raising a ``KeyError``.

        .. versionadded:: 0.11
        """
        if default is _sentinel:
            return self.__dict__.pop(name)
        else:
            return self.__dict__.pop(name, default)

    def setdefault(self, name: str, default: t.Any = None) -> t.Any:
        """Get the value of an attribute if it is present, otherwise
        set and return a default value. Like :meth:`dict.setdefault`.

        :param name: Name of attribute to get.
        :param default: Value to set and return if the attribute is not
            present.

        .. versionadded:: 0.11
        """
        return self.__dict__.setdefault(name, default)

    def __contains__(self, item: str) -> bool:
        return item in self.__dict__

    def __iter__(self) -> t.Iterator[str]:
        return iter(self.__dict__)

    def __repr__(self) -> str:
        ctx = _cv_app.get(None)
        if ctx is not None:
            return f"<flask.g of '{ctx.app.name}'>"
        return object.__repr__(self)


def after_this_request(
    f: ft.AfterRequestCallable[t.Any],
) -> ft.AfterRequestCallable[t.Any]:
    """Executes a function after this request.  This is useful to modify
    response objects.  The function is passed the response object and has
    to return the same or a new one.

    Example::

        @app.route('/')
        def index():
            @after_this_request
            def add_header(response):
                response.headers['X-Foo'] = 'Parachute'
                return response
            return 'Hello World!'

    This is more useful if a function other than the view function wants to
    modify a response.  For instance think of a decorator that wants to add
    some headers without converting the return value into a response object.

    .. versionadded:: 0.9
    """
    ctx = _cv_request.get(None)

    if ctx is None:
        raise RuntimeError(
            "'after_this_request' can only be used when a request"
            " context is active, such as in a view function."
        )

    ctx._after_request_functions.append(f)
    return f


F = t.TypeVar("F", bound=t.Callable[..., t.Any])


def copy_current_request_context(f: F) -> F:
    """A helper function that decorates a function to retain the current
    request context.  This is useful when working with greenlets.  The moment
    the function is decorated a copy of the request context is created and
    then pushed when the function is called.  The current session is also
    included in the copied request context.

    Example::

        import gevent
        from flask import copy_current_request_context

        @app.route('/')
        def index():
            @copy_current_request_context
            def do_some_work():
                # do some work here, it can access flask.request or
                # flask.session like you would otherwise in the view function.
                ...
            gevent.spawn(do_some_work)
            return 'Regular response'

    .. versionadded:: 0.10
    """
    ctx = _cv_request.get(None)

    if ctx is None:
        raise RuntimeError(
            "'copy_current_request_context' can only be used when a"
            " request context is active, such as in a view function."
        )

    ctx = ctx.copy()

    def wrapper(*args: t.Any, **kwargs: t.Any) -> t.Any:
        with ctx:  # type: ignore[union-attr]
            return ctx.app.ensure_sync(f)(*args, **kwargs)  # type: ignore[union-attr]

    return update_wrapper(wrapper, f)  # type: ignore[return-value]


def has_request_context() -> bool:
    """Deprecated. Use has_execution_context() instead."""
    warnings.warn(
        "'has_request_context' is deprecated and will be removed in Flask 4.0. "
        "Use 'has_execution_context' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return has_execution_context()


def has_app_context() -> bool:
    """Deprecated. Use has_execution_context() instead."""
    warnings.warn(
        "'has_app_context' is deprecated and will be removed in Flask 4.0. "
        "Use 'has_execution_context' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return has_execution_context()


def has_execution_context() -> bool:
    """Check if an execution context is active."""
    return _cv_execution.get(None) is not None


class ExecutionContext:
    """A unified context that combines application and request contexts.
    This is the new way to handle context in Flask, replacing the separate
    app and request contexts.
    """

    def __init__(
        self,
        app: Flask,
        environ: WSGIEnvironment | None = None,
        request: Request | None = None,
        session: SessionMixin | None = None,
    ) -> None:
        self.app = app
        self.url_adapter = app.create_url_adapter(None)
        self.g: _AppCtxGlobals = app.app_ctx_globals_class()
        self._cv_token: Optional[contextvars.Token[Optional[ExecutionContext]]] = None

        # Request-specific attributes
        self.environ = environ
        self.request = request
        self.session = session
        self._after_request_functions: list[ft.AfterRequestCallable[t.Any]] = []

        # Track if this is a request context
        self._is_request_context = request is not None

    def push(self) -> None:
        """Push this context to the stack."""
        if self._cv_token is not None:
            raise RuntimeError("Context is already pushed")

        self._cv_token = _cv_execution.set(self)

        if self._is_request_context:
            # For backward compatibility, also set the old context vars
            _cv_app.set(self)
            _cv_request.set(self)
            appcontext_pushed.send(self.app)
        else:
            _cv_app.set(self)

    def pop(self, exc: BaseException | None = _sentinel) -> None:  # type: ignore
        """Pop this context from the stack."""
        if self._cv_token is None:
            raise RuntimeError("Context is not pushed")

        if exc is _sentinel:
            exc = sys.exc_info()[1]

        if self._is_request_context and self.request is not None:
            # Run request teardown functions
            for func in reversed(self._after_request_functions):
                if hasattr(self.request, 'response'):
                    self.app.ensure_sync(func)(self.request.response)
            request_tearing_down.send(self.app, exc=exc)

        # Run app teardown functions
        for func in reversed(self.app.teardown_appcontext_funcs):
            self.app.ensure_sync(func)(exc)

        appcontext_popped.send(self.app)

        # Reset context vars
        if self._cv_token is not None:
            token = cast(contextvars.Token[Optional[ExecutionContext]], self._cv_token)
            _cv_execution.reset(token)
            self._cv_token = None

            if self._is_request_context:
                _cv_app.reset(token)
                _cv_request.reset(token)
            else:
                _cv_app.reset(token)

    def __enter__(self) -> ExecutionContext:
        self.push()
        return self

    def __exit__(
        self,
        exc_type: type | None,
        exc_value: BaseException | None,
        tb: TracebackType | None,
    ) -> None:
        self.pop(exc_value)

    def __repr__(self) -> str:
        return f"<ExecutionContext {self.app.name!r}>"
