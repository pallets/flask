
Context locals
================================================================================

Context local objects ("context locals") are global objects that manage data
specific to the current greenlet or thread ("the context"). Flask uses
context locals, like ``request``, ``session``, ``current_app``, and ``g``, for
data related to the current request ("the request context"). These objects are
only available when the application is processing a request.

Motivation
--------------------------------------------------------------------------------

Some web frameworks, like Django, require you to pass data specific to the
current request ("the request context") throughout your code in order to stay
thread-safe. This is inconvenient since it can make application logic verbose
and difficult to understand; many functions will need to take a ``request``
parameter and many will only pass it through to other calls. [2]_

One common solution to this problem is to make the request context globally
available. In fact, Django does this in several modules.  For example, Django's
internalization module inspects the current request to determine the current
language is. [2]_ And the database often keeps data around depending on the
current transaction. [2]_ However, globals introduce two new problems.  First,
they risk making large applications unmaintainable. Second, they aren't thread
safe.

Flask aims to make it quick and easy to write a traditional web application.
[1]_ So, while globals can make a large application hard to maintain, Flask
considers this out of the scope of the project. (Further, with responsible use
it should be possible to tame the complexities of these globals; they do not
manage state and are all singletons-- that is, there is one ``request`` per
request).

The standard way to make globals thread-safe is to use thread local storage,
which Python has supported via ``threading.local()`` since 2.4. However,
thread locals are not viable in web applications for two reasons. First, WSGI
does not guarantee that every request will get its own thread; web servers may
reuse threads for requests, which could pollute the thread local object and leak
memory. Second, some popular web servers, like Gunicorn, handle concurrency
without threads. Flask solves both of these problems by taking advantage of
context local objects from Werkzeug; global objects that manage data specific to
the current request.

The request runtime state
--------------------------------------------------------------------------------

A Flask application uses a context manager to handle entry into, and exit from,
the request context. The application creates a new request context and binds it
to the current context when it receives a new HTTP request which lasts until the
application responds [*]_::

    class Flask(_PackageBoundObject):
        ...
        def wsgi_app(self, environ, start_response):
            with self.request_context(environ):
                try:
                    response = self.full_dispatch_request()
                except Exception as e:
                    response = self.make_response(self.handle_exception(e))
                return response(environ, start_response)

We can see how request contexts work in more detail via the interpreter::

    >>> from flask import Flask, current_app, g, request, session
    >>> app = Flask('app1')

A Flask application starts in the *application setup state* when the
:class:`Flask` object is instantiated. The application may be configured in this
state, but it must not use any request globals::

    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)
    >>> request.url
    Traceback (most recent call last):
      File "<stdin>", line 1, in <module>
      File "/Library/Python/2.7/site-packages/werkzeug/local.py", line 338, in __getattr__
        return getattr(self._get_current_object(), name)
      File "/Library/Python/2.7/site-packages/werkzeug/local.py", line 297, in _get_current_object
        return self.__local()
      File "/Library/Python/2.7/site-packages/flask/globals.py", line 20, in _lookup_req_object
        raise RuntimeError('working outside of request context')
    RuntimeError: working outside of request context

When the application receives a request, the application transitions to the
*request runtime state* and it may access the request globals::

    >>> with app.test_request_context():
    ...   request
    ...   session
    ...   current_app
    ...   g
    ...
    <Request 'http://localhost/' [GET]>
    <NullSession {}>
    <Flask 'app1'>
    <flask.g of 'app1'>

The application returns to the application setup state after processing the
request::

    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)

The application runtime state
--------------------------------------------------------------------------------

The programmer can cause the application to transition into the *application
runtime state* in which only ``current_app`` and ``g`` are available by creating
an *application context*::

    >>> from flask import Flask, current_app, g, request, session, url_for
    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)
    >>> app = Flask('app1')
    >>> app.config['SERVER_NAME'] = 'myapp.dev:5000'
    >>> app.add_url_rule("/x", endpoint="x")
    >>> with app.app_context():
    ...   request
    ...   session
    ...   current_app
    ...   g
    ...   url_for('x')
    ...
    <LocalProxy unbound>
    <LocalProxy unbound>
    <Flask 'app1'>
    <flask.g of 'app1'>
    'http://myapp.dev:5000/x'

This state is useful for scripts, tests, and interactive sessions where the
programmer may wish to access data related to a database or the application
configuration without incurring the expense of faking a request.

Flask applications implicitly create an application context whenever they create
a request context, so any data available in an application context is also
available in a request context::

    >>> with app.test_request_context():
    ...   current_app
    ...   g
    ...   url_for('x')
    ...
    <Flask 'app1'>
    <flask.g of 'app1'>
    'http://myapp.dev:5000/x'

Implementation
--------------------------------------------------------------------------------

Flask internally maintains both the request context and the application context
as global ``LocalStack`` objects from Werkzeug. Their data are maintained
implemented as ``LocalProxy`` objects::

    from werkzeug.local import LocalStack, LocalProxy

    # context locals
    _request_ctx_stack = LocalStack()
    _app_ctx_stack = LocalStack()
    request = LocalProxy(lambda: _request_ctx_stack.top.request)
    session = LocalProxy(lambda: _request_ctx_stack.top.session)
    current_app = LocalProxy(lambda: _app_ctx_stack.top.app)
    g = LocalProxy(lambda: _app_ctx_stack.top.g)

There are two important things to know about ``LocalStack`` and ``LocalProxy``,
which are best explained with an example::

    >>> from werkzeug.local import LocalProxy, LocalStack
    >>> mydata = LocalStack()
    >>> mydata.top
    None
    >>> number = LocalProxy(lambda: mydata.top)
    >>> number
    None
    >>> mydata.push(42)
    [42]
    >>> mydata.top
    42
    >>> number
    42

First, we get different data if we access their data in a different context::

    >>> log = []
    >>> def f():
    ...   log.append(number)
    ...   mydata.push(11)
    ...   log.append(number)
    ...
    >>> import threading
    >>> thread = threading.Thread(target=f)
    >>> thread.start()
    >>> thread.join()
    >>> log
    [None, 11]

Second, changing their data in one context doesn't affect data in another::

    >>> number
    42

Notice that these stack objects can only hold one value at a time. Flask gets
around this by storing object on each stack: ``RequestContext`` objects, which
manage ``request`` and ``session`` on ``_request_ctx_stack``, and ``AppContext``
objects, which manage ``current_app`` and ``g`` on ``_app_ctx_stack``::

    from .globals import _request_ctx_stack, _app_ctx_stack

    class RequestContext(object):
        def __init__(self, app, environ):
            self.app = app
            self.request = app.request_class(environ)
            self.session = app.open_session(self.request)

        def push(self):
            # Before we push the request context we have to ensure that there
            # is an application context.
            app_ctx = _app_ctx_stack.top
            if app_ctx is None or app_ctx.app != self.app:
                app_ctx = self.app.app_context()
                app_ctx.push()
                self._implicit_app_ctx_stack.append(app_ctx)
            else:
                self._implicit_app_ctx_stack.append(None)

            _request_ctx_stack.push(self)

        def pop(self):
            app_ctx = self._implicit_app_ctx_stack.pop()

            _request_ctx_stack.pop()

            if app_ctx is not None:
                app_ctx.pop()

        def __enter__(self):
            self.push()
            return self

        def __exit__(self, exc_type, exc_value, tb):
            self.pop()

    class AppContext(object):
        def __init__(self, app):
            self.app = app
            self.g = app.app_ctx_globals_class()

        def push(self):
            _app_ctx_stack.push(self)

        def pop(self):
            _app_ctx_stack.pop()

        def __enter__(self):
            self.push()
            return self

        def __exit__(self, exc_type, exc_value, tb):
            self.pop()

Both ``RequestContext`` and ``AppContext`` are context managers. Therefore, both
can be invoked with the ``with`` statement, which is how a Flask application
invokes them::

    from .ctx import RequestContext

    class Flask(_PackageBoundObject):
        ...
        def app_context(self):
            return AppContext(self)

        def request_context(self, environ):
            return RequestContext(self, environ)

        def wsgi_app(self, environ, start_response):
            with self.request_context(environ):
                try:
                    response = self.full_dispatch_request()
                except Exception as e:
                    response = self.make_response(self.handle_exception(e))
                return response(environ, start_response)

However, they can also be used by directly invoking ``push()`` (which binds them
to the current context) and ``pop()`` (which does the opposite), which is more
useful for playing in the console::

    >>> from flask import Flask, current_app
    >>> app = Flask('x')
    >>> ctx = app.app_context()
    >>> ctx
    <flask.ctx.AppContext object at 0x110359190>
    >>> current_app
    <LocalProxy unbound>
    >>> ctx.push()
    >>> current_app
    <Flask 'x'>
    >>> ctx.pop()
    >>> current_app
    <LocalProxy unbound>

Footnotes
--------------------------------------------------------------------------------

.. [*]
    This was changed in
    https://github.com/mitsuhiko/flask/commit/f1918093ac70d589a4d67af0d77140734c06c13d

.. [1] http://flask.pocoo.org/docs/design/

.. [2]
    Ronacher. 2011. "Opening the Flask".

    Slides: http://mitsuhiko.pocoo.org/flask-pycon-2011.pdf

    Presentation: http://blip.tv/pycon-us-videos-2009-2010-2011/pycon-2011-opening-the-flask-4896892

    #. Flask's Design - 11:05.

    #. Context Locals - 11:25
