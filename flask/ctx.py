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
from .module import blueprint_is_module


class _RequestGlobals(object):
    pass


def has_request_context():
    """If you have code that wants to test if a request context is there or
    not this function can be used.  For instance if you want to take advantage
    of request information is it's available but fail silently if the request
    object is unavailable.

    ::

        class User(db.Model):

            def __init__(self, username, remote_addr=None):
                self.username = username
                if remote_addr is None and has_request_context():
                    remote_addr = request.remote_addr
                self.remote_addr = remote_addr

    Alternatively you can also just test any of the context bound objects
    (such as :class:`request` or :class:`g` for truthness)::

        class User(db.Model):

            def __init__(self, username, remote_addr=None):
                self.username = username
                if remote_addr is None and request:
                    remote_addr = request.remote_addr
                self.remote_addr = remote_addr

    .. versionadded:: 0.7
    """
    return _request_ctx_stack.top is not None


class RequestContext(object):
    """The request context contains all request relevant information.  It is
    created at the beginning of the request and pushed to the
    `_request_ctx_stack` and removed at the end of it.  It will create the
    URL adapter and request object for the WSGI environment provided.

    Do not attempt to use this class directly, instead use
    :meth:`~flask.Flask.test_request_context` and
    :meth:`~flask.Flask.request_context` to create this object.

    When the request context is popped, it will evaluate all the
    functions registered on the application for teardown execution
    (:meth:`~flask.Flask.teardown_request`).

    The request context is automatically popped at the end of the request
    for you.  In debug mode the request context is kept around if
    exceptions happen so that interactive debuggers have a chance to
    introspect the data.  With 0.4 this can also be forced for requests
    that did not fail and outside of `DEBUG` mode.  By setting
    ``'flask._preserve_context'`` to `True` on the WSGI environment the
    context will not pop itself at the end of the request.  This is used by
    the :meth:`~flask.Flask.test_client` for example to implement the
    deferred cleanup functionality.

    You might find this helpful for unittests where you need the
    information from the context local around for a little longer.  Make
    sure to properly :meth:`~werkzeug.LocalStack.pop` the stack yourself in
    that situation, otherwise your unittests will leak memory.
    """

    def __init__(self, app, environ):
        self.app = app
        self.request = app.request_class(environ)
        self.url_adapter = app.create_url_adapter(self.request)
        self.g = _RequestGlobals()
        self.flashes = None
        self.session = None

        self.match_request()

        # Support for deprecated functionality.  This is doing away with
        # Flask 1.0
        blueprint = self.request.blueprint
        if blueprint is not None:
            # better safe than sorry, we don't want to break code that
            # already worked
            bp = app.blueprints.get(blueprint)
            if bp is not None and blueprint_is_module(bp):
                self.request._is_old_module = True

    def match_request(self):
        """Can be overridden by a subclass to hook into the matching
        of the request.
        """
        try:
            url_rule, self.request.view_args = \
                self.url_adapter.match(return_rule=True)
            self.request.url_rule = url_rule
        except HTTPException, e:
            self.request.routing_exception = e

    def push(self):
        """Binds the request context to the current context."""
        _request_ctx_stack.push(self)

        # Open the session at the moment that the request context is
        # available. This allows a custom open_session method to use the
        # request context (e.g. flask-sqlalchemy).
        self.session = self.app.open_session(self.request)
        if self.session is None:
            self.session = _NullSession()

    def pop(self):
        """Pops the request context and unbinds it by doing that.  This will
        also trigger the execution of functions registered by the
        :meth:`~flask.Flask.teardown_request` decorator.
        """
        self.app.do_teardown_request()
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
           (tb is None or not self.app.preserve_context_on_exception):
            self.pop()
