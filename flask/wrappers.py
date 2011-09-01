# -*- coding: utf-8 -*-
"""
    flask.wrappers
    ~~~~~~~~~~~~~~

    Implements the WSGI wrappers (request and response).

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.wrappers import Request as RequestBase, Response as ResponseBase
from werkzeug.exceptions import BadRequest
from werkzeug.utils import cached_property

from .debughelpers import attach_enctype_error_multidict
from .helpers import json, _assert_have_json
from .globals import _request_ctx_stack


class Request(RequestBase):
    """The request object used by default in Flask.  Remembers the
    matched endpoint and view arguments.

    It is what ends up as :class:`~flask.request`.  If you want to replace
    the request object used you can subclass this and set
    :attr:`~flask.Flask.request_class` to your subclass.

    The request object is a :class:`~werkzeug.wrappers.Request` subclass and
    provides all of the attributes Werkzeug defines plus a few Flask
    specific ones.
    """

    #: the internal URL rule that matched the request.  This can be
    #: useful to inspect which methods are allowed for the URL from
    #: a before/after handler (``request.url_rule.methods``) etc.
    #:
    #: .. versionadded:: 0.6
    url_rule = None

    #: a dict of view arguments that matched the request.  If an exception
    #: happened when matching, this will be `None`.
    view_args = None

    #: if matching the URL failed, this is the exception that will be
    #: raised / was raised as part of the request handling.  This is
    #: usually a :exc:`~werkzeug.exceptions.NotFound` exception or
    #: something similar.
    routing_exception = None

    # switched by the request context until 1.0 to opt in deprecated
    # module functionality
    _is_old_module = False

    @property
    def max_content_length(self):
        """Read-only view of the `MAX_CONTENT_LENGTH` config key."""
        ctx = _request_ctx_stack.top
        if ctx is not None:
            return ctx.app.config['MAX_CONTENT_LENGTH']

    @property
    def endpoint(self):
        """The endpoint that matched the request.  This in combination with
        :attr:`view_args` can be used to reconstruct the same or a
        modified URL.  If an exception happened when matching, this will
        be `None`.
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

    @cached_property
    def json(self):
        """If the mimetype is `application/json` this will contain the
        parsed JSON data.  Otherwise this will be `None`.

        This requires Python 2.6 or an installed version of simplejson.
        """
        if __debug__:
            _assert_have_json()
        if self.mimetype == 'application/json':
            request_charset = self.mimetype_params.get('charset')
            try:
                if request_charset is not None:
                    return json.loads(self.data, encoding=request_charset)
                return json.loads(self.data)
            except ValueError, e:
                return self.on_json_loading_failed(e)

    def on_json_loading_failed(self, e):
        """Called if decoding of the JSON data failed.  The return value of
        this method is used by :attr:`json` when an error ocurred.  The
        default implementation raises a :class:`~werkzeug.exceptions.BadRequest`.

        .. versionadded:: 0.8
        """
        raise BadRequest()

    def _load_form_data(self):
        RequestBase._load_form_data(self)

        # in debug mode we're replacing the files multidict with an ad-hoc
        # subclass that raises a different error for key errors.
        ctx = _request_ctx_stack.top
        if ctx is not None and ctx.app.debug and \
           self.mimetype != 'multipart/form-data' and not self.files:
            attach_enctype_error_multidict(self)


class Response(ResponseBase):
    """The response object that is used by default in Flask.  Works like the
    response object from Werkzeug but is set to have an HTML mimetype by
    default.  Quite often you don't have to create this object yourself because
    :meth:`~flask.Flask.make_response` will take care of that for you.

    If you want to replace the response object used you can subclass this and
    set :attr:`~flask.Flask.response_class` to your subclass.
    """
    default_mimetype = 'text/html'
