
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

Application states
--------------------------------------------------------------------------------

A Flask application is in one of three states. Request globals are only
available in certain states. It is an error for an application to attempt to
access a request global in an inappropriate state, and the application will
throw a ``RuntimeError`` if this happens.

The initial state is the *application setup state* which begins when the
:class:`Flask` object is instantiated. The application may be configured in this
state, but it must not use any request globals::

    >>> from flask import Flask, current_app, g, request, session
    >>> app = Flask(__name__)
    >>> app.config['SERVER_NAME'] = 'myapp.dev:5000'
    >>> app.add_url_rule("/", endpoint="hello")
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
*request runtime state* and binds a new request context to the current context::

    class Flask(_PackageBoundObject):
        ...
        def wsgi_app(self, environ, start_response):
            with self.request_context(environ):
                try:
                    response = self.full_dispatch_request()
                except Exception as e:
                    response = self.make_response(self.handle_exception(e))
                return response(environ, start_response)

The application may access the request globals in this state::

    >>> with app.test_request_context():
    ...   request
    ...   session
    ...   current_app
    ...   g
    ...
    <Request 'http://localhost/' [GET]>
    <NullSession {}>
    <Flask '__main__'>
    <flask.g of '__main__'>

The application returns to the application setup state after processing the
request::

    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)

The application enters the *application runtime state* when an *application
context* is created. In this state, only ``current_app`` and ``g`` are
available::

    >>> with app.app_context():
    ...   request
    ...   session
    ...   current_app
    ...   g
    ...   url_for('hello')
    ...
    <LocalProxy unbound>
    <LocalProxy unbound>
    <Flask '__main__'>
    <flask.g of '__main__'>
    'http://myapp.dev:5000/'

This state is useful for scripts, tests, and interactive sessions where the
programmer may wish to access data related to a database or the application
configuration without incurring the expense of faking a request. For example,
Flaskr uses an application context to initialize the database::

    class FlaskrTestCase(unittest.TestCase):

        def setUp(self):
            """Before each test, set up a blank database"""
            self.db_fd, flaskr.app.config['DATABASE'] = tempfile.mkstemp()
            flaskr.app.config['TESTING'] = True
            self.app = flaskr.app.test_client()
            with flaskr.app.app_context():
                flaskr.init_db()

The application implicitly creates an application context whenever it creates a
request context, so any data available in an application context is also
available in a request context::

    >>> with app.test_request_context():
    ...   current_app
    ...   g
    ...   url_for('x')
    ...
    <Flask '__main__'>
    <flask.g of '__main__'>
    'http://myapp.dev:5000/'

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

Notice that ``LocalStack`` objects can only hold one value at a time, but that
we have two stacks, both of which need to maintain two values. We can solve this
by storing objects on each stack, since objects can hold multiple values. So, we
introduce ``RequestContext`` to manage ``request`` and ``session`` on the
request context stack and ``AppContext`` to manage ``current_app`` and ``g`` on
the application context stack::


    class AppContext(object):
        def __init__(self, app):
            self.app = app
            self.g = app.app_ctx_globals_class()
            ...
        ...

    class RequestContext(object):
        def __init__(self, app, environ):
            self.request = app.request_class(environ)
            self.session = app.open_session(self.request)
            ...
        ...

If we stopped here, we could use the either context with something like the
following code::

    ctx = RequestContext(app, environ)
    _request_ctx_stack.push(ctx)
    try:
        BLOCK
    finally:
        _request_ctx_stack.pop(ctx)

However, repeating this code in every function that uses a context is error
prone and make refactoring difficult. [3]_ We can eliminate this pattern by
implementing the context management protocol, which allow us invoke a context
using the ``with`` statement::

    from .globals import _request_ctx_stack, _app_ctx_stack

    class AppContext(object):
        ...

        def push(self):
            _app_ctx_stack.push(self)

        def pop(self):
            _app_ctx_stack.pop()

        def __enter__(self):
            self.push()
            return self

        def __exit__(self, exc_type, exc_value, tb):
            self.pop()

    class RequestContext(object):
        ...

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
            _request_ctx_stack.pop()

            app_ctx = self._implicit_app_ctx_stack.pop()
            if app_ctx is not None:
                app_ctx.pop()

        def __enter__(self):
            self.push()
            return self

        def __exit__(self, exc_type, exc_value, tb):
            self.pop()

Notice that each context also provides the ``push()`` (which binds it to the
current context) and ``pop()`` (which does the opposite) methods, which are
useful for playing in the console::

    >>> from flask import Flask, current_app
    >>> app = Flask(__name__)
    >>> ctx = app.app_context()
    >>> ctx
    <flask.ctx.AppContext object at 0x110359190>
    >>> current_app
    <LocalProxy unbound>
    >>> ctx.push()
    >>> current_app
    <Flask '__main__'>
    >>> ctx.pop()
    >>> current_app
    <LocalProxy unbound>

Finally, we reach the Flask application which simply creates a request context
for every new request::

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

Footnotes
--------------------------------------------------------------------------------

.. [1] http://flask.pocoo.org/docs/design/

.. [2]
    Ronacher. 2011. "Opening the Flask".

    Slides: http://mitsuhiko.pocoo.org/flask-pycon-2011.pdf

    Presentation: http://blip.tv/pycon-us-videos-2009-2010-2011/pycon-2011-opening-the-flask-4896892

    #. Flask's Design - 11:05.

    #. Context Locals - 11:25

.. [3]
    Guido van Rossum. 2005. PEP 340 -- Anonymous Block Statements.
    http://legacy.python.org/dev/peps/pep-0340/
