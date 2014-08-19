
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
internalization module inspects the current respects to figure out what the
current language is. [2]_ And the database often keeps data around depending on
the current transaction. [2]_ However, globals introduce two new problems.
First, they risk making large applications unmaintainable. Second, they aren't
thread safe.

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
the current greenlet or thread ("the context").

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

Flask starts in the *application setup state* when the :class:`Flask` object is
instantiated. In this state, the programmer may safely configure the application
and every context local is free::

    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)

Trying to use a context local in this state will result in a ``RuntimeError``::

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

When a request comes in, Flask transitions to the *request runtime state* in
which every context local is bound::

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

Finally, when the request is handled, Flask transitions back to the application
state::

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
