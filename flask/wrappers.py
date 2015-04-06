# -*- coding: utf-8 -*-
"""
    flask.wrappers
    ~~~~~~~~~~~~~~

    Implements the WSGI wrappers (request and response).

    :copyright: (c) 2015 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.wrappers import Request as RequestBase, Response as ResponseBase
from werkzeug.exceptions import BadRequest

from . import json
from .globals import _app_ctx_stack

_missing = object()


class JSONMixin(object):
    """Mixin for both request and response classes to provide JSON parsing
    capabilities.

    .. versionadded:: 0.12
    """

    @property
    def is_json(self):
        """Indicates if this request/response is JSON or not.  By default it
        is considered to include JSON data if the mimetype is
        :mimetype:`application/json` or :mimetype:`application/*+json`.
        """
        mt = self.mimetype
        if mt == 'application/json':
            return True
        if mt.startswith('application/') and mt.endswith('+json'):
            return True
        return False

    @property
    def json(self):
        """If the mimetype is :mimetype:`application/json` this will contain the
        parsed JSON data.  Otherwise this will be ``None``.

        The :meth:`get_json` method should be used instead.
        """
        from warnings import warn
        warn(DeprecationWarning('json is deprecated.  '
                                'Use get_json() instead.'), stacklevel=2)
        return self.get_json()

    def _get_data_for_json(self, cache):
        getter = getattr(self, 'get_data', None)
        if getter is not None:
            return getter(cache=cache)
        return self.data

    def get_json(self, force=False, silent=False, cache=True):
        """Parses the incoming JSON request data and returns it.  By default
        this function will return ``None`` if the mimetype is not
        :mimetype:`application/json` but this can be overridden by the
        ``force`` parameter. If parsing fails the
        :meth:`on_json_loading_failed` method on the request object will be
        invoked.

        :param force: if set to ``True`` the mimetype is ignored.
        :param silent: if set to ``True`` this method will fail silently
                       and return ``None``.
        :param cache: if set to ``True`` the parsed JSON data is remembered
                      on the request.
        """
        rv = getattr(self, '_cached_json', _missing)
        if rv is not _missing:
            return rv

        if not (force or self.is_json):
            return None

        # We accept a request charset against the specification as certain
        # clients have been using this in the past.  For responses, we assume
        # that if the response charset was set explicitly then the data had
        # been encoded correctly as well.
        charset = self.mimetype_params.get('charset')
        try:
            data = self._get_data_for_json(cache)
            if charset is not None:
                rv = json.loads(data, encoding=charset)
            else:
                rv = json.loads(data)
        except ValueError as e:
            if silent:
                rv = None
            else:
                rv = self.on_json_loading_failed(e)
        if cache:
            self._cached_json = rv
        return rv

    def on_json_loading_failed(self, e):
        """Called if decoding of the JSON data failed.  The return value of
        this method is used by :meth:`get_json` when an error occurred.  The
        default implementation just raises a :class:`BadRequest` exception.

        .. versionchanged:: 0.10
           Removed buggy previous behavior of generating a random JSON
           response.  If you want that behavior back you can trivially
           add it by subclassing.

        .. versionadded:: 0.8
        """
        ctx = _app_ctx_stack.top
        if ctx is not None and ctx.app.debug:
            raise BadRequest('Failed to decode JSON object: {0}'.format(e))
        raise BadRequest()


class Request(RequestBase, JSONMixin):
    """The request object used by default in Flask.  Remembers the
    matched endpoint and view arguments.

    It is what ends up as :class:`~flask.request`.  If you want to replace
    the request object used you can subclass this and set
    :attr:`~flask.Flask.request_class` to your subclass.

    The request object is a :class:`~werkzeug.wrappers.Request` subclass and
    provides all of the attributes Werkzeug defines plus a few Flask
    specific ones.
    """

    #: The internal URL rule that matched the request.  This can be
    #: useful to inspect which methods are allowed for the URL from
    #: a before/after handler (``request.url_rule.methods``) etc.
    #:
    #: .. versionadded:: 0.6
    url_rule = None

    #: A dict of view arguments that matched the request.  If an exception
    #: happened when matching, this will be ``None``.
    view_args = None

    #: If matching the URL failed, this is the exception that will be
    #: raised / was raised as part of the request handling.  This is
    #: usually a :exc:`~werkzeug.exceptions.NotFound` exception or
    #: something similar.
    routing_exception = None

    # Switched by the request context until 1.0 to opt in deprecated
    # module functionality.
    _is_old_module = False

    @property
    def max_content_length(self):
        """Read-only view of the ``MAX_CONTENT_LENGTH`` config key."""
        ctx = _app_ctx_stack.top
        if ctx is not None:
            return ctx.app.config['MAX_CONTENT_LENGTH']

    @property
    def endpoint(self):
        """The endpoint that matched the request.  This in combination with
        :attr:`view_args` can be used to reconstruct the same or a
        modified URL.  If an exception happened when matching, this will
        be ``None``.
        """
        if self.url_rule is not None:
            return self.url_rule.endpoint

    @property
    def module(self):
        """The name of the current module if the request was dispatched
        to an actual module.  This is deprecated functionality, use blueprints
        instead.
        """
        from warnings import warn
        warn(DeprecationWarning('modules were deprecated in favor of '
                                'blueprints.  Use request.blueprint '
                                'instead.'), stacklevel=2)
        if self._is_old_module:
            return self.blueprint

    @property
    def blueprint(self):
        """The name of the current blueprint"""
        if self.url_rule and '.' in self.url_rule.endpoint:
            return self.url_rule.endpoint.rsplit('.', 1)[0]

    def _load_form_data(self):
        RequestBase._load_form_data(self)

        # In debug mode we're replacing the files multidict with an ad-hoc
        # subclass that raises a different error for key errors.
        ctx = _app_ctx_stack.top
        if ctx is not None and ctx.app.debug and \
           self.mimetype != 'multipart/form-data' and not self.files:
            from .debughelpers import attach_enctype_error_multidict
            attach_enctype_error_multidict(self)


class Response(ResponseBase, JSONMixin):
    """The response object that is used by default in Flask.  Works like the
    response object from Werkzeug but is set to have an HTML mimetype by
    default.  Quite often you don't have to create this object yourself because
    :meth:`~flask.Flask.make_response` will take care of that for you.

    If you want to replace the response object used you can subclass this and
    set :attr:`~flask.Flask.response_class` to your subclass.
    """
    default_mimetype = 'text/html'

    def _get_data_for_json(self, cache):
        getter = getattr(self, 'get_data', None)
        if getter is not None:
            # Ignore the cache flag since response doesn't support it
            return getter()
        return self.data
