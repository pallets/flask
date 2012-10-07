# -*- coding: utf-8 -*-
"""
    flask.exceptions
    ~~~~~~~~~~~~

    Flask specific additions to :class:`~werkzeug.exceptions.HTTPException`

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""
from werkzeug.exceptions import HTTPException, BadRequest
from . import json


class JSONHTTPException(HTTPException):
    """A base class for HTTP exceptions with ``Content-Type:
    application/json``.

    The ``description`` attribute of this class must set to a string (*not* an
    HTML string) which describes the error.

    """

    def get_body(self, environ):
        """Overrides :meth:`werkzeug.exceptions.HTTPException.get_body` to
        return the description of this error in JSON format instead of HTML.

        """
        return json.dumps(dict(description=self.get_description(environ)))

    def get_headers(self, environ):
        """Returns a list of headers including ``Content-Type:
        application/json``.

        """
        return [('Content-Type', 'application/json')]


class JSONBadRequest(JSONHTTPException, BadRequest):
    """Represents an HTTP ``400 Bad Request`` error whose body contains an
    error message in JSON format instead of HTML format (as in the superclass).
    """

    #: The description of the error which occurred as a string.
    description = (
        'The browser (or proxy) sent a request that this server could not '
        'understand.'
    )
