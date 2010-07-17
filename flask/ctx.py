# -*- coding: utf-8 -*-
"""
    flask.ctx
    ~~~~~~~~~

    Implements the objects required to keep the context.

    :copyright: (c) 2010 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

from werkzeug.exceptions import HTTPException

from .globals import _request_ctx_stack
from .session import _NullSession


class _RequestGlobals(object):
    pass


class _RequestContext(object):
    """The request context contains all request relevant information.  It is
    created at the beginning of the request and pushed to the
    `_request_ctx_stack` and removed at the end of it.  It will create the
    URL adapter and request object for the WSGI environment provided.
    """

    def __init__(self, app, environ):
        self.app = app
        self.request = app.request_class(environ)
        self.url_adapter = app.create_url_adapter(self.request)
        self.session = app.open_session(self.request)
        if self.session is None:
            self.session = _NullSession()
        self.g = _RequestGlobals()
        self.flashes = None

        try:
            url_rule, self.request.view_args = \
                self.url_adapter.match(return_rule=True)
            self.request.url_rule = url_rule
        except HTTPException, e:
            self.request.routing_exception = e

    def push(self):
        """Binds the request context."""
        _request_ctx_stack.push(self)

    def pop(self):
        """Pops the request context."""
        _request_ctx_stack.pop()

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        # do not pop the request stack if we are in debug mode and an
        # exception happened.  This will allow the debugger to still
        # access the request object in the interactive shell.  Furthermore
        # the context can be force kept alive for the test client.
        # See flask.testing for how this works.
        if not self.request.environ.get('flask._preserve_context') and \
           (tb is None or not self.app.debug):
            self.pop()
