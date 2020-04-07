import io
import json as _json
import uuid
import warnings
from datetime import date
from datetime import datetime

from markupsafe import Markup
from werkzeug.http import http_date

from ..globals import current_app
from ..globals import request

try:
    import dataclasses
except ImportError:
    # Python < 3.7
    dataclasses = None


class JSONEncoder(_json.JSONEncoder):
    """The default Flask JSON encoder. This one extends the default
    encoder by also supporting ``datetime``, ``UUID``, ``dataclasses``,
    and ``Markup`` objects.

    ``datetime`` objects are serialized as RFC 822 datetime strings.
    This is the same as the HTTP date format.

    In order to support more data types, override the :meth:`default`
    method.
    """

    def default(self, o):
        """Implement this method in a subclass such that it returns a
        serializable object for ``o``, or calls the base implementation (to
        raise a :exc:`TypeError`).

        For example, to support arbitrary iterators, you could implement
        default like this::

            def default(self, o):
                try:
                    iterable = iter(o)
                except TypeError:
                    pass
                else:
                    return list(iterable)
                return JSONEncoder.default(self, o)
        """
        if isinstance(o, datetime):
            return http_date(o.utctimetuple())
        if isinstance(o, date):
            return http_date(o.timetuple())
        if isinstance(o, uuid.UUID):
            return str(o)
        if dataclasses and dataclasses.is_dataclass(o):
            return dataclasses.asdict(o)
        if hasattr(o, "__html__"):
            return str(o.__html__())
        return super().default(self, o)


class JSONDecoder(_json.JSONDecoder):
    """The default JSON decoder.  This one does not change the behavior from
    the default decoder.  Consult the :mod:`json` documentation
    for more information.  This decoder is not only used for the load
    functions of this module but also :attr:`~flask.Request`.
    """


def _dump_arg_defaults(kwargs, app=None):
    """Inject default arguments for dump functions."""
    if app is None:
        app = current_app

    if app:
        bp = app.blueprints.get(request.blueprint) if request else None
        cls = bp.json_encoder if bp and bp.json_encoder else app.json_encoder
        kwargs.setdefault("cls", cls)
        kwargs.setdefault("ensure_ascii", app.config["JSON_AS_ASCII"])
        kwargs.setdefault("sort_keys", app.config["JSON_SORT_KEYS"])
    else:
        kwargs.setdefault("sort_keys", True)
        kwargs.setdefault("cls", JSONEncoder)


def _load_arg_defaults(kwargs, app=None):
    """Inject default arguments for load functions."""
    if app is None:
        app = current_app

    if app:
        bp = app.blueprints.get(request.blueprint) if request else None
        cls = bp.json_decoder if bp and bp.json_decoder else app.json_decoder
        kwargs.setdefault("cls", cls)
    else:
        kwargs.setdefault("cls", JSONDecoder)


def dumps(obj, app=None, **kwargs):
    """Serialize ``obj`` to a JSON-formatted string. If there is an
    app context pushed, use the current app's configured encoder
    (:attr:`~flask.Flask.json_encoder`), or fall back to the default
    :class:`JSONEncoder`.

    Takes the same arguments as the built-in :func:`json.dumps`, and
    does some extra configuration based on the application.

    :param obj: Object to serialize to JSON.
    :param app: App instance to use to configure the JSON encoder.
        Uses ``current_app`` if not given, and falls back to the default
        encoder when not in an app context.
    :param kwargs: Extra arguments passed to :func:`json.dumps`.

    .. versionchanged:: 1.0.3

        ``app`` can be passed directly, rather than requiring an app
        context for configuration.
    """
    _dump_arg_defaults(kwargs, app=app)
    encoding = kwargs.pop("encoding", None)
    rv = _json.dumps(obj, **kwargs)

    if encoding is not None:
        warnings.warn(
            "'encoding' is deprecated and will be removed in 2.1.",
            DeprecationWarning,
            stacklevel=2,
        )

        if isinstance(rv, str):
            return rv.encode(encoding)

    return rv


def dump(obj, fp, app=None, **kwargs):
    """Like :func:`dumps` but writes into a file object."""
    _dump_arg_defaults(kwargs, app=app)
    encoding = kwargs.pop("encoding", None)
    show_warning = encoding is not None

    try:
        fp.write("")
    except TypeError:
        show_warning = True
        fp = io.TextIOWrapper(fp, encoding or "utf-8")

    if show_warning:
        warnings.warn(
            "Writing to a binary file, and the 'encoding' argument, is"
            " deprecated and will be removed in 2.1.",
            DeprecationWarning,
            stacklevel=2,
        )

    _json.dump(obj, fp, **kwargs)


def loads(s, app=None, **kwargs):
    """Deserialize an object from a JSON-formatted string ``s``. If
    there is an app context pushed, use the current app's configured
    decoder (:attr:`~flask.Flask.json_decoder`), or fall back to the
    default :class:`JSONDecoder`.

    Takes the same arguments as the built-in :func:`json.loads`, and
    does some extra configuration based on the application.

    :param s: JSON string to deserialize.
    :param app: App instance to use to configure the JSON decoder.
        Uses ``current_app`` if not given, and falls back to the default
        encoder when not in an app context.
    :param kwargs: Extra arguments passed to :func:`json.dumps`.

    .. versionchanged:: 1.0.3

        ``app`` can be passed directly, rather than requiring an app
        context for configuration.
    """
    _load_arg_defaults(kwargs, app=app)
    encoding = kwargs.pop("encoding", None)

    if encoding is not None:
        warnings.warn(
            "'encoding' is deprecated and will be removed in 2.1. The"
            " data must be a string or UTF-8 bytes.",
            DeprecationWarning,
            stacklevel=2,
        )

        if isinstance(s, bytes):
            s = s.decode(encoding)

    return _json.loads(s, **kwargs)


def load(fp, app=None, **kwargs):
    """Like :func:`loads` but reads from a file object."""
    _load_arg_defaults(kwargs, app=app)
    encoding = kwargs.pop("encoding", None)

    if encoding is not None:
        warnings.warn(
            "'encoding' is deprecated and will be removed in 2.1. The"
            " file must be text mode, or binary mode with UTF-8 bytes.",
            DeprecationWarning,
            stacklevel=2,
        )

        if isinstance(fp.read(0), bytes):
            fp = io.TextIOWrapper(fp, encoding)

    return _json.load(fp, **kwargs)


_htmlsafe_map = str.maketrans(
    {"<": "\\u003c", ">": "\\u003e", "&": "\\u0026", "'": "\\u0027"}
)


def htmlsafe_dumps(obj, **kwargs):
    """Works exactly like :func:`dumps` but is safe for use in ``<script>``
    tags.  It accepts the same arguments and returns a JSON string.  Note that
    this is available in templates through the ``|tojson`` filter which will
    also mark the result as safe.  Due to how this function escapes certain
    characters this is safe even if used outside of ``<script>`` tags.

    The following characters are escaped in strings:

    -   ``<``
    -   ``>``
    -   ``&``
    -   ``'``

    This makes it safe to embed such strings in any place in HTML with the
    notable exception of double quoted attributes.  In that case single
    quote your attributes or HTML escape it in addition.

    .. versionchanged:: 0.10
       This function's return value is now always safe for HTML usage, even
       if outside of script tags or if used in XHTML.  This rule does not
       hold true when using this function in HTML attributes that are double
       quoted.  Always single quote attributes if you use the ``|tojson``
       filter.  Alternatively use ``|tojson|forceescape``.
    """
    return dumps(obj, **kwargs).translate(_htmlsafe_map)


def htmlsafe_dump(obj, fp, **kwargs):
    """Like :func:`htmlsafe_dumps` but writes into a file object."""
    fp.write(htmlsafe_dumps(obj, **kwargs))


def jsonify(*args, **kwargs):
    """This function wraps :func:`dumps` to add a few enhancements that make
    life easier.  It turns the JSON output into a :class:`~flask.Response`
    object with the :mimetype:`application/json` mimetype.  For convenience, it
    also converts multiple arguments into an array or multiple keyword arguments
    into a dict.  This means that both ``jsonify(1,2,3)`` and
    ``jsonify([1,2,3])`` serialize to ``[1,2,3]``.

    For clarity, the JSON serialization behavior has the following differences
    from :func:`dumps`:

    1. Single argument: Passed straight through to :func:`dumps`.
    2. Multiple arguments: Converted to an array before being passed to
       :func:`dumps`.
    3. Multiple keyword arguments: Converted to a dict before being passed to
       :func:`dumps`.
    4. Both args and kwargs: Behavior undefined and will throw an exception.

    Example usage::

        from flask import jsonify

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


    .. versionchanged:: 0.11
        Added support for serializing top-level arrays. This introduces
        a security risk in ancient browsers. See :ref:`security-json`
        for details.

    This function's response will be pretty printed if the
    ``JSONIFY_PRETTYPRINT_REGULAR`` config parameter is set to True or the
    Flask app is running in debug mode. Compressed (not pretty) formatting
    currently means no indents and no spaces after separators.

    .. versionadded:: 0.2
    """
    indent = None
    separators = (",", ":")

    if current_app.config["JSONIFY_PRETTYPRINT_REGULAR"] or current_app.debug:
        indent = 2
        separators = (", ", ": ")

    if args and kwargs:
        raise TypeError("jsonify() behavior undefined when passed both args and kwargs")
    elif len(args) == 1:  # single args are passed directly to dumps()
        data = args[0]
    else:
        data = args or kwargs

    return current_app.response_class(
        f"{dumps(data, indent=indent, separators=separators)}\n",
        mimetype=current_app.config["JSONIFY_MIMETYPE"],
    )


def tojson_filter(obj, **kwargs):
    return Markup(htmlsafe_dumps(obj, **kwargs))
