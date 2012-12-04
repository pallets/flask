.. _request-context:

The Request Context
===================

This document describes the behavior in Flask 0.7 which is mostly in line
with the old behavior but has some small, subtle differences.

It is recommended that you read the :ref:`app-context` chapter first.

Diving into Context Locals
--------------------------

Say you have a utility function that returns the URL the user should be
redirected to.  Imagine it would always redirect to the URL's ``next``
parameter or the HTTP referrer or the index page::

    from flask import request, url_for

    def redirect_url():
        return request.args.get('next') or \
               request.referrer or \
               url_for('index')

As you can see, it accesses the request object.  If you try to run this
from a plain Python shell, this is the exception you will see:

>>> redirect_url()
Traceback (most recent call last):
  File "<stdin>", line 1, in <module>
AttributeError: 'NoneType' object has no attribute 'request'

That makes a lot of sense because we currently do not have a request we
could access.  So we have to make a request and bind it to the current
context.  The :attr:`~flask.Flask.test_request_context` method can create
us a :class:`~flask.ctx.RequestContext`:

>>> ctx = app.test_request_context('/?next=http://example.com/')

This context can be used in two ways.  Either with the `with` statement
or by calling the :meth:`~flask.ctx.RequestContext.push` and
:meth:`~flask.ctx.RequestContext.pop` methods:

>>> ctx.push()

From that point onwards you can work with the request object:

>>> redirect_url()
u'http://example.com/'

Until you call `pop`:

>>> ctx.pop()

Because the request context is internally maintained as a stack you can
push and pop multiple times.  This is very handy to implement things like
internal redirects.

For more information of how to utilize the request context from the
interactive Python shell, head over to the :ref:`shell` chapter.

How the Context Works
---------------------

If you look into how the Flask WSGI application internally works, you will
find a piece of code that looks very much like this::

    def wsgi_app(self, environ):
        with self.request_context(environ):
            try:
                response = self.full_dispatch_request()
            except Exception, e:
                response = self.make_response(self.handle_exception(e))
            return response(environ, start_response)

The method :meth:`~Flask.request_context` returns a new
:class:`~flask.ctx.RequestContext` object and uses it in combination with
the `with` statement to bind the context.  Everything that is called from
the same thread from this point onwards until the end of the `with`
statement will have access to the request globals (:data:`flask.request`
and others).

The request context internally works like a stack: The topmost level on
the stack is the current active request.
:meth:`~flask.ctx.RequestContext.push` adds the context to the stack on
the very top, :meth:`~flask.ctx.RequestContext.pop` removes it from the
stack again.  On popping the application's
:func:`~flask.Flask.teardown_request` functions are also executed.

Another thing of note is that the request context will automatically also
create an :ref:`application context <app-context>` when it's pushed and
there is no application context for that application so far.

.. _callbacks-and-errors:

Callbacks and Errors
--------------------

What happens if an error occurs in Flask during request processing?  This
particular behavior changed in 0.7 because we wanted to make it easier to
understand what is actually happening.  The new behavior is quite simple:

1.  Before each request, :meth:`~flask.Flask.before_request` functions are
    executed.  If one of these functions return a response, the other
    functions are no longer called.  In any case however the return value
    is treated as a replacement for the view's return value.

2.  If the :meth:`~flask.Flask.before_request` functions did not return a
    response, the regular request handling kicks in and the view function
    that was matched has the chance to return a response.

3.  The return value of the view is then converted into an actual response
    object and handed over to the :meth:`~flask.Flask.after_request`
    functions which have the chance to replace it or modify it in place.

4.  At the end of the request the :meth:`~flask.Flask.teardown_request`
    functions are executed.  This always happens, even in case of an
    unhandled exception down the road or if a before-request handler was
    not executed yet or at all (for example in test environments sometimes
    you might want to not execute before-request callbacks).

Now what happens on errors?  In production mode if an exception is not
caught, the 500 internal server handler is called.  In development mode
however the exception is not further processed and bubbles up to the WSGI
server.  That way things like the interactive debugger can provide helpful
debug information.

An important change in 0.7 is that the internal server error is now no
longer post processed by the after request callbacks and after request
callbacks are no longer guaranteed to be executed.  This way the internal
dispatching code looks cleaner and is easier to customize and understand.

The new teardown functions are supposed to be used as a replacement for
things that absolutely need to happen at the end of request.

Teardown Callbacks
------------------

The teardown callbacks are special callbacks in that they are executed at
at different point.  Strictly speaking they are independent of the actual
request handling as they are bound to the lifecycle of the
:class:`~flask.ctx.RequestContext` object.  When the request context is
popped, the :meth:`~flask.Flask.teardown_request` functions are called.

This is important to know if the life of the request context is prolonged
by using the test client in a with statement or when using the request
context from the command line::

    with app.test_client() as client:
        resp = client.get('/foo')
        # the teardown functions are still not called at that point
        # even though the response ended and you have the response
        # object in your hand

    # only when the code reaches this point the teardown functions
    # are called.  Alternatively the same thing happens if another
    # request was triggered from the test client

It's easy to see the behavior from the command line:

>>> app = Flask(__name__)
>>> @app.teardown_request
... def teardown_request(exception=None):
...     print 'this runs after request'
...
>>> ctx = app.test_request_context()
>>> ctx.push()
>>> ctx.pop()
this runs after request
>>>

Keep in mind that teardown callbacks are always executed, even if
before-request callbacks were not executed yet but an exception happened.
Certain parts of the test system might also temporarily create a request
context without calling the before-request handlers.  Make sure to write
your teardown-request handlers in a way that they will never fail.

.. _notes-on-proxies:

Notes On Proxies
----------------

Some of the objects provided by Flask are proxies to other objects.  The
reason behind this is that these proxies are shared between threads and
they have to dispatch to the actual object bound to a thread behind the
scenes as necessary.

Most of the time you don't have to care about that, but there are some
exceptions where it is good to know that this object is an actual proxy:

-   The proxy objects do not fake their inherited types, so if you want to
    perform actual instance checks, you have to do that on the instance
    that is being proxied (see `_get_current_object` below).
-   if the object reference is important (so for example for sending
    :ref:`signals`)

If you need to get access to the underlying object that is proxied, you
can use the :meth:`~werkzeug.local.LocalProxy._get_current_object` method::

    app = current_app._get_current_object()
    my_signal.send(app)

Context Preservation on Error
-----------------------------

If an error occurs or not, at the end of the request the request context
is popped and all data associated with it is destroyed.  During
development however that can be problematic as you might want to have the
information around for a longer time in case an exception occurred.  In
Flask 0.6 and earlier in debug mode, if an exception occurred, the
request context was not popped so that the interactive debugger can still
provide you with important information.

Starting with Flask 0.7 you have finer control over that behavior by
setting the ``PRESERVE_CONTEXT_ON_EXCEPTION`` configuration variable.  By
default it's linked to the setting of ``DEBUG``.  If the application is in
debug mode the context is preserved, in production mode it's not.

Do not force activate ``PRESERVE_CONTEXT_ON_EXCEPTION`` in production mode
as it will cause your application to leak memory on exceptions.  However
it can be useful during development to get the same error preserving
behavior as in development mode when attempting to debug an error that
only occurs under production settings.
