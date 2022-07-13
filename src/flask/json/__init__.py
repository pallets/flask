from __future__ import annotations

import json as _json
import typing as t

from jinja2.utils import htmlsafe_json_dumps as _jinja_htmlsafe_dumps

from ..globals import current_app
from .provider import _default

if t.TYPE_CHECKING:  # pragma: no cover
    from ..app import Flask
    from ..wrappers import Response


class JSONEncoder(_json.JSONEncoder):
    """The default JSON encoder. Handles extra types compared to the
    built-in :class:`json.JSONEncoder`.

    -   :class:`datetime.datetime` and :class:`datetime.date` are
        serialized to :rfc:`822` strings. This is the same as the HTTP
        date format.
    -   :class:`decimal.Decimal` is serialized to a string.
    -   :class:`uuid.UUID` is serialized to a string.
    -   :class:`dataclasses.dataclass` is passed to
        :func:`dataclasses.asdict`.
    -   :class:`~markupsafe.Markup` (or any object with a ``__html__``
        method) will call the ``__html__`` method to get a string.

    Assign a subclass of this to :attr:`flask.Flask.json_encoder` or
    :attr:`flask.Blueprint.json_encoder` to override the default.

    .. deprecated:: 2.2
        Will be removed in Flask 2.3. Use ``app.json`` instead.
    """

    def __init__(self, **kwargs) -> None:
        import warnings

        warnings.warn(
            "'JSONEncoder' is deprecated and will be removed in"
            " Flask 2.3. Use 'Flask.json' to provide an alternate"
            " JSON implementation instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        super().__init__(**kwargs)

    def default(self, o: t.Any) -> t.Any:
        """Convert ``o`` to a JSON serializable type. See
        :meth:`json.JSONEncoder.default`. Python does not support
        overriding how basic types like ``str`` or ``list`` are
        serialized, they are handled before this method.
        """
        return _default(o)


class JSONDecoder(_json.JSONDecoder):
    """The default JSON decoder.

    This does not change any behavior from the built-in
    :class:`json.JSONDecoder`.

    Assign a subclass of this to :attr:`flask.Flask.json_decoder` or
    :attr:`flask.Blueprint.json_decoder` to override the default.

    .. deprecated:: 2.2
        Will be removed in Flask 2.3. Use ``app.json`` instead.
    """

    def __init__(self, **kwargs) -> None:
        import warnings

        warnings.warn(
            "'JSONDecoder' is deprecated and will be removed in"
            " Flask 2.3. Use 'Flask.json' to provide an alternate"
            " JSON implementation instead.",
            DeprecationWarning,
            stacklevel=3,
        )
        super().__init__(**kwargs)


def dumps(obj: t.Any, *, app: Flask | None = None, **kwargs: t.Any) -> str:
    """Serialize data as JSON.

    If :data:`~flask.current_app` is available, it will use its
    :meth:`app.json.dumps() <flask.json.provider.JSONProvider.dumps>`
    method, otherwise it will use :func:`json.dumps`.

    :param obj: The data to serialize.
    :param kwargs: Arguments passed to the ``dumps`` implementation.

    .. versionchanged:: 2.2
        Calls ``current_app.json.dumps``, allowing an app to override
        the behavior.

    .. versionchanged:: 2.2
        The ``app`` parameter will be removed in Flask 2.3.

    .. versionchanged:: 2.0.2
        :class:`decimal.Decimal` is supported by converting to a string.

    .. versionchanged:: 2.0
        ``encoding`` will be removed in Flask 2.1.

    .. versionchanged:: 1.0.3
        ``app`` can be passed directly, rather than requiring an app
        context for configuration.
    """
    if app is not None:
        import warnings

        warnings.warn(
            "The 'app' parameter is deprecated and will be removed in"
            " Flask 2.3. Call 'app.json.dumps' directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    else:
        app = current_app

    if app:
        return app.json.dumps(obj, **kwargs)

    kwargs.setdefault("default", _default)
    return _json.dumps(obj, **kwargs)


def dump(
    obj: t.Any, fp: t.IO[str], *, app: Flask | None = None, **kwargs: t.Any
) -> None:
    """Serialize data as JSON and write to a file.

    If :data:`~flask.current_app` is available, it will use its
    :meth:`app.json.dump() <flask.json.provider.JSONProvider.dump>`
    method, otherwise it will use :func:`json.dump`.

    :param obj: The data to serialize.
    :param fp: A file opened for writing text. Should use the UTF-8
        encoding to be valid JSON.
    :param kwargs: Arguments passed to the ``dump`` implementation.

    .. versionchanged:: 2.2
        Calls ``current_app.json.dump``, allowing an app to override
        the behavior.

    .. versionchanged:: 2.2
        The ``app`` parameter will be removed in Flask 2.3.

    .. versionchanged:: 2.0
        Writing to a binary file, and the ``encoding`` argument, will be
        removed in Flask 2.1.
    """
    if app is not None:
        import warnings

        warnings.warn(
            "The 'app' parameter is deprecated and will be removed in"
            " Flask 2.3. Call 'app.json.dump' directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    else:
        app = current_app

    if app:
        app.json.dump(obj, fp, **kwargs)
    else:
        kwargs.setdefault("default", _default)
        _json.dump(obj, fp, **kwargs)


def loads(s: str | bytes, *, app: Flask | None = None, **kwargs: t.Any) -> t.Any:
    """Deserialize data as JSON.

    If :data:`~flask.current_app` is available, it will use its
    :meth:`app.json.loads() <flask.json.provider.JSONProvider.loads>`
    method, otherwise it will use :func:`json.loads`.

    :param s: Text or UTF-8 bytes.
    :param kwargs: Arguments passed to the ``loads`` implementation.

    .. versionchanged:: 2.2
        Calls ``current_app.json.loads``, allowing an app to override
        the behavior.

    .. versionchanged:: 2.2
        The ``app`` parameter will be removed in Flask 2.3.

    .. versionchanged:: 2.0
        ``encoding`` will be removed in Flask 2.1. The data must be a
        string or UTF-8 bytes.

    .. versionchanged:: 1.0.3
        ``app`` can be passed directly, rather than requiring an app
        context for configuration.
    """
    if app is not None:
        import warnings

        warnings.warn(
            "The 'app' parameter is deprecated and will be removed in"
            " Flask 2.3. Call 'app.json.loads' directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    else:
        app = current_app

    if app:
        return app.json.loads(s, **kwargs)

    return _json.loads(s, **kwargs)


def load(fp: t.IO[t.AnyStr], *, app: Flask | None = None, **kwargs: t.Any) -> t.Any:
    """Deserialize data as JSON read from a file.

    If :data:`~flask.current_app` is available, it will use its
    :meth:`app.json.load() <flask.json.provider.JSONProvider.load>`
    method, otherwise it will use :func:`json.load`.

    :param fp: A file opened for reading text or UTF-8 bytes.
    :param kwargs: Arguments passed to the ``load`` implementation.

    .. versionchanged:: 2.2
        Calls ``current_app.json.load``, allowing an app to override
        the behavior.

    .. versionchanged:: 2.2
        The ``app`` parameter will be removed in Flask 2.3.

    .. versionchanged:: 2.0
        ``encoding`` will be removed in Flask 2.1. The file must be text
        mode, or binary mode with UTF-8 bytes.
    """
    if app is not None:
        import warnings

        warnings.warn(
            "The 'app' parameter is deprecated and will be removed in"
            " Flask 2.3. Call 'app.json.load' directly instead.",
            DeprecationWarning,
            stacklevel=2,
        )
    else:
        app = current_app

    if app:
        return app.json.load(fp, **kwargs)

    return _json.load(fp, **kwargs)


def htmlsafe_dumps(obj: t.Any, **kwargs: t.Any) -> str:
    """Serialize an object to a string of JSON with :func:`dumps`, then
    replace HTML-unsafe characters with Unicode escapes and mark the
    result safe with :class:`~markupsafe.Markup`.

    This is available in templates as the ``|tojson`` filter.

    The returned string is safe to render in HTML documents and
    ``<script>`` tags. The exception is in HTML attributes that are
    double quoted; either use single quotes or the ``|forceescape``
    filter.

    .. deprecated:: 2.2
        Will be removed in Flask 2.3. This is built-in to Jinja now.

    .. versionchanged:: 2.0
        Uses :func:`jinja2.utils.htmlsafe_json_dumps`. The returned
        value is marked safe by wrapping in :class:`~markupsafe.Markup`.

    .. versionchanged:: 0.10
        Single quotes are escaped, making this safe to use in HTML,
        ``<script>`` tags, and single-quoted attributes without further
        escaping.
    """
    import warnings

    warnings.warn(
        "'htmlsafe_dumps' is deprecated and will be removed in Flask"
        " 2.3. Use 'jinja2.utils.htmlsafe_json_dumps' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    return _jinja_htmlsafe_dumps(obj, dumps=dumps, **kwargs)


def htmlsafe_dump(obj: t.Any, fp: t.IO[str], **kwargs: t.Any) -> None:
    """Serialize an object to JSON written to a file object, replacing
    HTML-unsafe characters with Unicode escapes. See
    :func:`htmlsafe_dumps` and :func:`dumps`.

    .. deprecated:: 2.2
        Will be removed in Flask 2.3.
    """
    import warnings

    warnings.warn(
        "'htmlsafe_dump' is deprecated and will be removed in Flask"
        " 2.3. Use 'jinja2.utils.htmlsafe_json_dumps' instead.",
        DeprecationWarning,
        stacklevel=2,
    )
    fp.write(htmlsafe_dumps(obj, **kwargs))


def jsonify(*args: t.Any, **kwargs: t.Any) -> Response:
    """Serialize the given arguments as JSON, and return a
    :class:`~flask.Response` object with the ``application/json``
    mimetype. A dict or list returned from a view will be converted to a
    JSON response automatically without needing to call this.

    This requires an active request or application context, and calls
    :meth:`app.json.response() <flask.json.provider.JSONProvider.response>`.

    In debug mode, the output is formatted with indentation to make it
    easier to read. This may also be controlled by the provider.

    Either positional or keyword arguments can be given, not both.
    If no arguments are given, ``None`` is serialized.

    :param args: A single value to serialize, or multiple values to
        treat as a list to serialize.
    :param kwargs: Treat as a dict to serialize.

    .. versionchanged:: 2.2
        Calls ``current_app.json.response``, allowing an app to override
        the behavior.

    .. versionchanged:: 2.0.2
        :class:`decimal.Decimal` is supported by converting to a string.

    .. versionchanged:: 0.11
        Added support for serializing top-level arrays. This was a
        security risk in ancient browsers. See :ref:`security-json`.

    .. versionadded:: 0.2
    """
    return current_app.json.response(*args, **kwargs)
