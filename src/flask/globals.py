from __future__ import annotations

import typing as t
from contextvars import ContextVar

from werkzeug.local import LocalProxy

if t.TYPE_CHECKING:  # pragma: no cover
    from .app import Flask
    from .ctx import _AppCtxGlobals
    from .ctx import AppContext
    from .sessions import SessionMixin
    from .wrappers import Request

    T = t.TypeVar("T", covariant=True)

    class ProxyMixin(t.Protocol[T]):
        def _get_current_object(self) -> T: ...

    # These subclasses inform type checkers that the proxy objects look like the
    # proxied type along with the _get_current_object method.
    class FlaskProxy(ProxyMixin[Flask], Flask): ...

    class AppContextProxy(ProxyMixin[AppContext], AppContext): ...

    class _AppCtxGlobalsProxy(ProxyMixin[_AppCtxGlobals], _AppCtxGlobals): ...

    class RequestProxy(ProxyMixin[Request], Request): ...

    class SessionMixinProxy(ProxyMixin[SessionMixin], SessionMixin): ...


_no_app_msg = """\
Working outside of application context.

Attempted to use functionality that expected a current application to be set. To
solve this, set up an app context using 'with app.app_context()'. See the
documentation on app context for more information.\
"""
_cv_app: ContextVar[AppContext] = ContextVar("flask.app_ctx")
app_ctx: AppContextProxy = LocalProxy(  # type: ignore[assignment]
    _cv_app, unbound_message=_no_app_msg
)
current_app: FlaskProxy = LocalProxy(  # type: ignore[assignment]
    _cv_app, "app", unbound_message=_no_app_msg
)
g: _AppCtxGlobalsProxy = LocalProxy(  # type: ignore[assignment]
    _cv_app, "g", unbound_message=_no_app_msg
)

_no_req_msg = """\
Working outside of request context.

Attempted to use functionality that expected an active HTTP request. See the
documentation on request context for more information.\
"""
request: RequestProxy = LocalProxy(  # type: ignore[assignment]
    _cv_app, "request", unbound_message=_no_req_msg
)
session: SessionMixinProxy = LocalProxy(  # type: ignore[assignment]
    _cv_app, "session", unbound_message=_no_req_msg
)


def __getattr__(name: str) -> t.Any:
    import warnings

    if name == "request_ctx":
        warnings.warn(
            "'request_ctx' has merged with 'app_ctx', and will be removed"
            " in Flask 4.0. Use 'app_ctx' instead.",
            DeprecationWarning,
            stacklevel=2,
        )
        return app_ctx

    raise AttributeError(name)
