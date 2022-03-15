import typing as t


if t.TYPE_CHECKING:
    from _typeshed.wsgi import WSGIApplication  # noqa: F401
    from werkzeug.datastructures import Headers  # noqa: F401
    from werkzeug.wrappers.response import Response  # noqa: F401

# The possible types that are directly convertible or are a Response object.
ResponseValue = t.Union[
    "Response",
    str,
    bytes,
    t.Dict[str, t.Any],  # any jsonify-able dict
    t.Iterator[str],
    t.Iterator[bytes],
]
StatusCode = int

# the possible types for an individual HTTP header
HeaderName = str
HeaderValue = t.Union[str, t.List[str], t.Tuple[str, ...]]

# the possible types for HTTP headers
HeadersValue = t.Union[
    "Headers", t.Dict[HeaderName, HeaderValue], t.List[t.Tuple[HeaderName, HeaderValue]]
]

# The possible types returned by a route function.
ResponseReturnValue = t.Union[
    ResponseValue,
    t.Tuple[ResponseValue, HeadersValue],
    t.Tuple[ResponseValue, StatusCode],
    t.Tuple[ResponseValue, StatusCode, HeadersValue],
    "WSGIApplication",
]

AppOrBlueprintKey = t.Optional[str]  # The App key is None, whereas blueprints are named
AfterRequestCallable = t.Callable[["Response"], "Response"]
BeforeFirstRequestCallable = t.Callable[[], None]
BeforeRequestCallable = t.Callable[[], t.Optional[ResponseReturnValue]]
TeardownCallable = t.Callable[[t.Optional[BaseException]], None]
TemplateContextProcessorCallable = t.Callable[[], t.Dict[str, t.Any]]
TemplateFilterCallable = t.Callable[..., t.Any]
TemplateGlobalCallable = t.Callable[..., t.Any]
TemplateTestCallable = t.Callable[..., bool]
URLDefaultCallable = t.Callable[[str, dict], None]
URLValuePreprocessorCallable = t.Callable[[t.Optional[str], t.Optional[dict]], None]
# This should take Exception, but that either breaks typing the argument
# with a specific exception, or decorating multiple times with different
# exceptions (and using a union type on the argument).
# https://github.com/pallets/flask/issues/4095
# https://github.com/pallets/flask/issues/4295
# https://github.com/pallets/flask/issues/4297
ErrorHandlerCallable = t.Callable[[t.Any], ResponseReturnValue]
