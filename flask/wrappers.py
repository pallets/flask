# -*- coding: utf-8 -*-
"""
    flask.wrappers
    ~~~~~~~~~~~~~~

    Implements the WSGI wrappers (request and response).

    :copyright: © 2010 by the Pallets team.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.exceptions import BadRequest
from werkzeug.wrappers import Request as RequestBase, Response as ResponseBase

from flask import json
from flask.globals import current_app


class JSONMixin(object):
    """Common mixin for both request and response objects to provide JSON
    parsing capabilities.

    .. versionadded:: 1.0
    """

    _cached_json = (Ellipsis, Ellipsis)

    @property
    def is_json(self):
        """Check if the mimetype indicates JSON data, either
        :mimetype:`application/json` or :mimetype:`application/*+json`.

        .. versionadded:: 0.11
        """
        mt = self.mimetype
        return (
            mt == 'application/json'
            or (mt.startswith('application/')) and mt.endswith('+json')
        )

    @property
    def json(self):
        """This will contain the parsed JSON data if the mimetype indicates
        JSON (:mimetype:`application/json`, see :meth:`is_json`), otherwise it
        will be ``None``.
        """
        return self.get_json()

    def _get_data_for_json(self, cache):
        return self.get_data(cache=cache)

    def get_json(self, force=False, silent=False, cache=True):
        """Parse and return the data as JSON. If the mimetype does not
        indicate JSON (:mimetype:`application/json`, see
        :meth:`is_json`), this returns ``None`` unless ``force`` is
        true. If parsing fails, :meth:`on_json_loading_failed` is called
        and its return value is used as the return value.

        :param force: Ignore the mimetype and always try to parse JSON.
        :param silent: Silence parsing errors and return ``None``
            instead.
        :param cache: Store the parsed JSON to return for subsequent
            calls.
        """
        if cache and self._cached_json[silent] is not Ellipsis:
            return self._cached_json[silent]

        if not (force or self.is_json):
            return None

        data = self._get_data_for_json(cache=cache)

        try:
            rv = json.loads(data)
        except ValueError as e:
            if silent:
                rv = None
                if cache:
                    normal_rv, _ = self._cached_json
                    self._cached_json = (normal_rv, rv)
            else:
                rv = self.on_json_loading_failed(e)
                if cache:
                    _, silent_rv = self._cached_json
                    self._cached_json = (rv, silent_rv)
        else:
            if cache:
                self._cached_json = (rv, rv)

        return rv

    def on_json_loading_failed(self, e):
        """Called if :meth:`get_json` parsing fails and isn't silenced. If
        this method returns a value, it is used as the return value for
        :meth:`get_json`. The default implementation raises a
        :class:`BadRequest` exception.

        .. versionchanged:: 0.10
           Raise a :exc:`BadRequest` error instead of returning an error
           message as JSON. If you want that behavior you can add it by
           subclassing.

        .. versionadded:: 0.8
        """
        if current_app is not None and current_app.debug:
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
    #: Though if the request's method was invalid for the URL rule,
    #: the valid list is available in ``routing_exception.valid_methods``
    #: instead (an attribute of the Werkzeug exception :exc:`~werkzeug.exceptions.MethodNotAllowed`)
    #: because the request was never internally bound.
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

    @property
    def max_content_length(self):
        """Read-only view of the ``MAX_CONTENT_LENGTH`` config key."""
        if current_app:
            return current_app.config['MAX_CONTENT_LENGTH']

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
    def blueprint(self):
        """The name of the current blueprint"""
        if self.url_rule and '.' in self.url_rule.endpoint:
            return self.url_rule.endpoint.rsplit('.', 1)[0]

    def _load_form_data(self):
        RequestBase._load_form_data(self)

        # In debug mode we're replacing the files multidict with an ad-hoc
        # subclass that raises a different error for key errors.
        if (
            current_app
            and current_app.debug
            and self.mimetype != 'multipart/form-data'
            and not self.files
        ):
            from .debughelpers import attach_enctype_error_multidict
            attach_enctype_error_multidict(self)


class Response(ResponseBase, JSONMixin):
    """The response object that is used by default in Flask.  Works like the
    response object from Werkzeug but is set to have an HTML mimetype by
    default.  Quite often you don't have to create this object yourself because
    :meth:`~flask.Flask.make_response` will take care of that for you.

    If you want to replace the response object used you can subclass this and
    set :attr:`~flask.Flask.response_class` to your subclass.

    .. versionchanged:: 1.0
        JSON support is added to the response, like the request. This is useful
        when testing to get the test client response data as JSON.

    .. versionchanged:: 1.0

        Added :attr:`max_cookie_size`.
    """

    default_mimetype = 'text/html'

    def _get_data_for_json(self, cache):
        return self.get_data()

    @property
    def max_cookie_size(self):
        """Read-only view of the :data:`MAX_COOKIE_SIZE` config key.

        See :attr:`~werkzeug.wrappers.BaseResponse.max_cookie_size` in
        Werkzeug's docs.
        """
        if current_app:
            return current_app.config['MAX_COOKIE_SIZE']

        # return Werkzeug's default when not in an app context
        return super(Response, self).max_cookie_size
