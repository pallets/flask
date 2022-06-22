import typing as t
from contextvars import ContextVar

from werkzeug.local import LocalProxy

if t.TYPE_CHECKING:  # pragma: no cover
    from .app import Flask
    from .ctx import _AppCtxGlobals
    from .ctx import AppContext
    from .ctx import RequestContext
    from .sessions import SessionMixin
    from .wrappers import Request

_request_ctx_err_msg = """\
Working outside of request context.

This typically means that you attempted to use functionality that needed
an active HTTP request.  Consult the documentation on testing for
information about how to avoid this problem.\
"""
_app_ctx_err_msg = """\
Working outside of application context.

This typically means that you attempted to use functionality that needed
to interface with the current application object in some way. To solve
this, set up an application context with app.app_context().  See the
documentation for more information.\
"""

_T = t.TypeVar("_T")


class CtxStack(t.Generic[_T]):
    def __init__(self, var: ContextVar[t.List[_T]], error: str) -> None:
        self.var = var
        self.error = error

    def push(self, ctx: _T) -> t.List[_T]:
        stack = self.var.get(None)

        if stack is None:
            stack = []
            self.var.set(stack)

        stack.append(ctx)
        return stack

    def pop(self) -> t.Optional[_T]:
        stack = self.var.get(None)

        if stack is None or len(stack) == 0:
            return None

        return stack.pop()

    @property
    def top(self) -> _T:
        stack = self.var.get(None)

        if stack is None or len(stack) == 0:
            return None

        return stack[-1]

    def require(self) -> _T:
        top = self.top

        if top is None:
            raise RuntimeError(self.error)

        return top


_app_var: ContextVar[t.List["AppContext"]] = ContextVar("_app_var")
_app_ctx_stack: CtxStack["AppContext"] = CtxStack(_app_var, _app_ctx_err_msg)
current_app: "Flask" = LocalProxy(lambda: _app_ctx_stack.require().app)  # type: ignore
g: "_AppCtxGlobals" = LocalProxy(lambda: _app_ctx_stack.require().g)  # type: ignore
_req_var: ContextVar[t.List["RequestContext"]] = ContextVar("_req_var")
_request_ctx_stack: CtxStack["RequestContext"] = CtxStack(
    _req_var, _request_ctx_err_msg
)
request: "Request" = LocalProxy(  # type: ignore
    lambda: _request_ctx_stack.require().request
)
session: "SessionMixin" = LocalProxy(  # type: ignore
    lambda: _request_ctx_stack.require().session
)
