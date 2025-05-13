from __future__ import annotations

import collections.abc as cabc
import typing as t

if t.TYPE_CHECKING:  # pragma: no cover
    from _typeshed.wsgi import WSGIApplication  # noqa: F401
    from werkzeug.datastructures import Headers  # noqa: F401
    from werkzeug.sansio.response import Response  # noqa: F401

# The possible types that are directly convertible or are a Response object.
ResponseValue = t.Union[
    "Response",
    str,
    bytes,
    list[t.Any],
    # Only dict is actually accepted, but Mapping allows for TypedDict.
    t.Mapping[str, t.Any],
    t.Iterator[str],
    t.Iterator[bytes],
    cabc.AsyncIterable[str],  # for Quart, until App is generic.
    cabc.AsyncIterable[bytes],
]

# the possible types for an individual HTTP header
HeaderValue = str | list[str] | tuple[str, ...]

# the possible types for HTTP headers
HeadersValue = t.Union[
    "Headers",
    t.Mapping[str, HeaderValue],
    t.Sequence[tuple[str, HeaderValue]],
]

# The possible types returned by a route function.
ResponseReturnValue = t.Union[
    ResponseValue,
    tuple[ResponseValue, HeadersValue],
    tuple[ResponseValue, int],
    tuple[ResponseValue, int, HeadersValue],
    "WSGIApplication",
]

# Allow any subclass of werkzeug.Response, such as the one from Flask,
# as a callback argument. Using werkzeug.Response directly makes a
# callback annotated with flask.Response fail type checking.
ResponseClass = t.TypeVar("ResponseClass", bound="Response")

AppOrBlueprintKey = str | None  # The App key is None, whereas blueprints are named
AfterRequestCallable = (
    t.Callable[[ResponseClass], ResponseClass]
    | t.Callable[[ResponseClass], t.Awaitable[ResponseClass]]
)
BeforeFirstRequestCallable = t.Callable[[], None] | t.Callable[[], t.Awaitable[None]]
BeforeRequestCallable = (
    t.Callable[[], ResponseReturnValue | None]
    | t.Callable[[], t.Awaitable[ResponseReturnValue | None]]
)
ShellContextProcessorCallable = t.Callable[[], dict[str, t.Any]]
TeardownCallable = (
    t.Callable[[BaseException | None], None]
    | t.Callable[[BaseException | None], t.Awaitable[None]]
)
TemplateContextProcessorCallable = (
    t.Callable[[], dict[str, t.Any]] | t.Callable[[], t.Awaitable[dict[str, t.Any]]]
)
TemplateFilterCallable = t.Callable[..., t.Any]
TemplateGlobalCallable = t.Callable[..., t.Any]
TemplateTestCallable = t.Callable[..., bool]
URLDefaultCallable = t.Callable[[str, dict[str, t.Any]], None]
URLValuePreprocessorCallable = t.Callable[[str | None, dict[str, t.Any] | None], None]

# This should take Exception, but that either breaks typing the argument
# with a specific exception, or decorating multiple times with different
# exceptions (and using a union type on the argument).
# https://github.com/pallets/flask/issues/4095
# https://github.com/pallets/flask/issues/4295
# https://github.com/pallets/flask/issues/4297
ErrorHandlerCallable = (
    t.Callable[[t.Any], ResponseReturnValue]
    | t.Callable[[t.Any], t.Awaitable[ResponseReturnValue]]
)

RouteCallable = (
    t.Callable[..., ResponseReturnValue]
    | t.Callable[..., t.Awaitable[ResponseReturnValue]]
)
