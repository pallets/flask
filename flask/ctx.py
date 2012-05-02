# -*- coding: utf-8 -*-
"""
    flask.ctx
    ~~~~~~~~~

    Implements the objects required to keep the context.

    :copyright: (c) 2011 by Armin Ronacher.
    :license: BSD, see LICENSE for more details.
"""

import sys

from werkzeug.exceptions import HTTPException

from .globals import _request_ctx_stack, _app_ctx_stack
from .module import blueprint_is_module


class _RequestGlobals(object):
    """A plain object."""
    pass


def _push_app_if_necessary(app):
    top = _app_ctx_stack.top
    if top is None or top.app != app:
        ctx = app.app_context()
        ctx.push()
        return ctx


def has_request_context():
    """If you have code that wants to test if a request context is there or
    not this function can be used.  For instance, you may want to take advantage
    of request information if the request object is available, but fail
    silently if it is unavailable.

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


def has_app_context():
    """Works like :func:`has_request_context` but for the application
    context.  You can also just do a boolean check on the
    :data:`current_app` object instead.

    .. versionadded:: 0.9
    """
    return _app_ctx_stack.top is not None


class AppContext(object):
    """The application context binds an application object implicitly
    to the current thread or greenlet, similar to how the
    :class:`RequestContext` binds request information.  The application
    context is also implicitly created if a request context is created
    but the application is not on top of the individual application
    context.
    """

    def __init__(self, app):
        self.app = app
        self.url_adapter = app.create_url_adapter(None)

    def push(self):
        """Binds the app context to the current context."""
        _app_ctx_stack.push(self)

    def pop(self, exc=None):
        """Pops the app context."""
        if exc is None:
            exc = sys.exc_info()[1]
        self.app.do_teardown_appcontext(exc)
        rv = _app_ctx_stack.pop()
        assert rv is self, 'Popped wrong app context.  (%r instead of %r)' \
            % (rv, self)

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        self.pop()


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
        self.g = app.request_globals_class()
        self.flashes = None
        self.session = None

        # indicator if the context was preserved.  Next time another context
        # is pushed the preserved context is popped.
        self.preserved = False

        # Indicates if pushing this request context also triggered the pushing
        # of an application context.  If it implicitly pushed an application
        # context, it will be stored there
        self._pushed_application_context = None

        self.match_request()

        # XXX: Support for deprecated functionality.  This is going away with
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
        # If an exception ocurrs in debug mode or if context preservation is
        # activated under exception situations exactly one context stays
        # on the stack.  The rationale is that you want to access that
        # information under debug situations.  However if someone forgets to
        # pop that context again we want to make sure that on the next push
        # it's invalidated otherwise we run at risk that something leaks
        # memory.  This is usually only a problem in testsuite since this
        # functionality is not active in production environments.
        top = _request_ctx_stack.top
        if top is not None and top.preserved:
            top.pop()

        # Before we push the request context we have to ensure that there
        # is an application context.
        self._pushed_application_context = _push_app_if_necessary(self.app)

        _request_ctx_stack.push(self)

        # Open the session at the moment that the request context is
        # available. This allows a custom open_session method to use the
        # request context (e.g. flask-sqlalchemy).
        self.session = self.app.open_session(self.request)
        if self.session is None:
            self.session = self.app.make_null_session()

    def pop(self, exc=None):
        """Pops the request context and unbinds it by doing that.  This will
        also trigger the execution of functions registered by the
        :meth:`~flask.Flask.teardown_request` decorator.

        .. versionchanged:: 0.9
           Added the `exc` argument.
        """
        self.preserved = False
        if exc is None:
            exc = sys.exc_info()[1]
        self.app.do_teardown_request(exc)
        rv = _request_ctx_stack.pop()
        assert rv is self, 'Popped wrong request context.  (%r instead of %r)' \
            % (rv, self)

        # get rid of circular dependencies at the end of the request
        # so that we don't require the GC to be active.
        rv.request.environ['werkzeug.request'] = None

        # Get rid of the app as well if necessary.
        if self._pushed_application_context:
            self._pushed_application_context.pop(exc)
            self._pushed_application_context = None

    def __enter__(self):
        self.push()
        return self

    def __exit__(self, exc_type, exc_value, tb):
        # do not pop the request stack if we are in debug mode and an
        # exception happened.  This will allow the debugger to still
        # access the request object in the interactive shell.  Furthermore
        # the context can be force kept alive for the test client.
        # See flask.testing for how this works.
        if self.request.environ.get('flask._preserve_context') or \
           (tb is not None and self.app.preserve_context_on_exception):
            self.preserved = True
        else:
            self.pop(exc_value)

    def __repr__(self):
        return '<%s \'%s\' [%s] of %s>' % (
            self.__class__.__name__,
            self.request.url,
            self.request.method,
            self.app.name
        )
