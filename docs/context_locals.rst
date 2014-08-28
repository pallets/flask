
Context locals
================================================================================

Context local objects ("context locals") are global objects that manage data
specific to the current greenlet or thread ("the context"). Flask uses
context locals, like ``request``, ``session``, ``current_app``, and ``g``, for
data related to the current request ("the request context"). These objects are
only available when the application is processing a request.

Motivation
--------------------------------------------------------------------------------

Some web frameworks, like Django, call view functions with data specific to the
current request ("the request context"). This is in order to stay thread-safe;
in these frameworks, view functions generate a response by passing the request
context throughout their logic.

The problem with this approach is that it can make application logic verbose and
opaque since many functions will depend on a request object only because they
call other functions which depend on it. [2]_ This explains why some Django
modules fetch the request context themselves. [*]_

Since every view will want access to the request context, one solution to this
problem is to make the request context globally available. However, globals
introduce three new problems. First, they risk making large applications
unmaintainable. Second, they aren't thread safe. Third, even if we can solve the
first two problems, the behavior of thread-safe global is complex.

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

Thread-safe globals do introduce complexity into Flask. Developers who are
unfamiliar with context local objects will need to carefully study the
documentation to understand how they work.

Application states
--------------------------------------------------------------------------------

Flask exposes four request globals, ``request``, ``session``, ``current_app``,
and ``g``, each of which is only available in certain application states. It is
an error for an application to attempt to access a request global in an
inappropriate state, and the application will throw a ``RuntimeError`` if this
happens.

There are three states that a Flask application can be in: the *application
setup state*, the *application runtime state*, and the *request runtime state*.

The application setup state
````````````````````````````````````````````````````````````````````````````````

In the *application setup state*, no request globals are available. This state
begins when the :class:`Flask` object is instantiated::

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

The application runtime state
````````````````````````````````````````````````````````````````````````````````

The application enters the *application runtime state* when an *application
context* is created. In this state, only ``current_app`` and ``g`` ("the
application context") are available::

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

The request runtime state
````````````````````````````````````````````````````````````````````````````````

In the *request runtime state*, the application has access to the application
context and the request context::

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

The application is in this state while processing a request::

    class Flask(_PackageBoundObject):
        ...
        def wsgi_app(self, environ, start_response):
            with self.request_context(environ):
                try:
                    response = self.full_dispatch_request()
                except Exception as e:
                    response = self.make_response(self.handle_exception(e))
                return response(environ, start_response)

Implementation
--------------------------------------------------------------------------------

Flask implements both the request context and the application context as global
``LocalStack`` objects from Werkzeug and implements each request global as a
global ``LocalProxy`` object::

    from werkzeug.local import LocalStack, LocalProxy

    # context locals
    _request_ctx_stack = LocalStack()
    _app_ctx_stack = LocalStack()
    request = LocalProxy(lambda: _request_ctx_stack.top.request)
    session = LocalProxy(lambda: _request_ctx_stack.top.session)
    current_app = LocalProxy(lambda: _app_ctx_stack.top.app)
    g = LocalProxy(lambda: _app_ctx_stack.top.g)

Since both contexts are stacks, you can ``push()`` and ``pop()`` them::

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
    >>> mydata.push(15)
    [42, 15]
    >>> mydata.top
    15
    >>> mydata.pop()
    15
    >>> mydata.top
    42

What's important to know about ``LocalStack`` is that each thread that accesses
its data has its own independent copy. Therefore, we get different data if
we access data in a different thread::

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

And, we get the same data even if we change data in a different thread::

    >>> number
    42

.. admonition:: Proxies

    The request globals are proxies to other objects. This is so because these
    objects are shared between threads. Proxies allow us to dispatch to the
    actual object bound to a thread as necessary. Most of the time you don't
    have to care about this, but there are some exceptions when this is
    important to know:

    - If you want to perform actual instance checks. Proxy objects do not fake their
      inherited types, so you have to do that on the instance that is being proxied.

    - If the object reference is important (for example, when sending :ref:`signals`)

    To access the underlying object that is being proxied, you can use the
    :meth:`~werkzeug.local.LocalProxy._get_current_object` method::

        app = current_app._get_current_object()
        my_signal.send(app)

``LocalStack`` objects can only hold one value at a time, but we have two
stacks, both of which need to maintain two values. We can solve this by storing
objects on each stack, since objects can hold multiple values. So, we introduce
``RequestContext`` to manage ``request`` and ``session`` on the request context
stack and ``AppContext`` to manage ``current_app`` and ``g`` on the application
context stack::

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

However, repeating this code in every function that uses a context would be
error prone and make refactoring difficult. [3]_ We can eliminate this pattern
by implementing the context management protocol, which allows us invoke a
context using the ``with`` statement::

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

.. [*]
    For example, Django's internalization module inspects the current request to
    determine the current language is. [2]_ And the database often keeps data
    around depending on the current transaction. [2]_

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
