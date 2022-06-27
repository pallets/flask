import typing as t
from contextvars import ContextVar

from werkzeug.local import LocalStack

if t.TYPE_CHECKING:  # pragma: no cover
    from .app import Flask
    from .ctx import _AppCtxGlobals
    from .ctx import AppContext
    from .ctx import RequestContext
    from .sessions import SessionMixin
    from .wrappers import Request

_no_app_msg = """\
Working outside of application context.

This typically means that you attempted to use functionality that needed
the current application. To solve this, set up an application context
with app.app_context(). See the documentation for more information.\
"""
_cv_app: ContextVar[t.List["AppContext"]] = ContextVar("flask.app_ctx")
_app_ctx_stack: LocalStack["AppContext"] = LocalStack(_cv_app)
app_ctx: "AppContext" = _app_ctx_stack(  # type: ignore[assignment]
    unbound_message=_no_app_msg
)
current_app: "Flask" = _app_ctx_stack(  # type: ignore[assignment]
    "app", unbound_message=_no_app_msg
)
g: "_AppCtxGlobals" = _app_ctx_stack(  # type: ignore[assignment]
    "g", unbound_message=_no_app_msg
)

_no_req_msg = """\
Working outside of request context.

This typically means that you attempted to use functionality that needed
an active HTTP request. Consult the documentation on testing for
information about how to avoid this problem.\
"""
_cv_req: ContextVar[t.List["RequestContext"]] = ContextVar("flask.request_ctx")
_request_ctx_stack: LocalStack["RequestContext"] = LocalStack(_cv_req)
request_ctx: "RequestContext" = _request_ctx_stack(  # type: ignore[assignment]
    unbound_message=_no_req_msg
)
request: "Request" = _request_ctx_stack(  # type: ignore[assignment]
    "request", unbound_message=_no_req_msg
)
session: "SessionMixin" = _request_ctx_stack(  # type: ignore[assignment]
    "session", unbound_message=_no_req_msg
)
