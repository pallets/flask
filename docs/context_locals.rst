
Context locals
================================================================================

Context-local objects ("context locals") are global objects that manage data
specific to the current greenlet or thread ("the context"). Flask uses
context-local objects, like ``request``, ``session``, ``g``, and
``current_app``, for information related to the current request and current
application. These objects are only available for the duration of a request.

Motivation
--------------------------------------------------------------------------------

Some frameworks, like Django, require you to pass information related to the
request around from function to function within a request in order to stay
thread-safe. This is inconvenient since it can make application logic verbose
and difficult to understand; many functions will need to take a ``request``
parameter and many will only pass it through to other calls. [2]_

One common solution to this problem is to make information related to the
request globally available. In fact, Django does this in several modules.  For
example, Django's internalization module inspects the current respects to figure
out what the current language is. [2]_  And the database often keeps data around
depending on the current transaction. [2]_ However, these instances are isolated
since globals introduces two new problems. First, they risk making large
applications unmaintainable. Second, they aren't thread safe.

Flask aims to make it quick and easy to write a traditional web application.
[1]_ So, while globals can make a large application hard to maintain, Flask
considers this out of the scope of the project. (Further, with responsible use
it should be possible to tame the complexities of these globals; they do not
manage state and are all singletons-- that is, there is one ``request`` per
request).

The typical solution to thread-safe globals is thread local storage, which
Python has supported via ``threading.local()`` since 2.4. However, thread-locals
are not viable in web applications for two reasons. First, WSGI does not
guarantee that every request will get its own thread; web servers may reuse
threads for requests, which could pollute the thread local object.  Second, some
popular web servers handle concurrency without threads. For example, Gunicorn_
uses greenlets. Flask solves both of these problems by introducing the *request
context* object that manages data specific to the current request in the current
thread or greenlet ("context").

The request context
--------------------------------------------------------------------------------

The *request context* is a context manager that handles entry into, and exit
from, a runtime environment containing all information relevant to the current
request. Flask creates a new request context and binds it to the current context
for the duration of a request whenever it receives a new HTTP request [*]_::

    class Flask(_PackageBoundObject):
        ...
        def wsgi_app(self, environ, start_response):
            with self.request_context(environ):
                try:
                    response = self.full_dispatch_request()
                except Exception as e:
                    response = self.make_response(self.handle_exception(e))
                return response(environ, start_response)

We can see how request contexts work in more detail via the interpreter. At
first, Flask begins in the *application state* where the application may be
configured and no context locals are bound::

    >>> from flask import Flask, request, session
    >>> app = Flask('app1')
    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)

Trying to use any of these objects in this state will result in a
``RuntimeError``::

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

When a request comes in, Flask transitions to the *runtime state* in which
every context local is bound::

    >>> with app.test_request_context():
    ...   current_app
    ...   g
    ...   request
    ...   session
    ...
    <Flask 'app1'>
    <flask.g of 'app1'>
    <Request 'http://localhost/' [GET]>
    <NullSession {}>

Finally, when the request is handled, Flask transitions back to the application
state::

    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)

The runtime state
--------------------------------------------------------------------------------

Flask 0.9 divided the runtime state into two parts: the *request runtime
state*, managed by a request context, and the *application runtime state*,
managed by an *application context*. The request context was restricted to
manage anything to do with a web browser, e.g. HTTP request data or HTTP
session data, and the application context took over managing anything to do with
connection pooling (e.g. database connection) or configuration management.

The advantage to this division is that it becomes possible to retrieve
information related to the current app, like ``current_app``, ``g``, and
``url_for``, without faking a request-- an expensive operation. For example::

    >>> from flask import Flask, current_app, g, request, session, url_for
    >>> current_app, g, request, session
    (<LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>, <LocalProxy unbound>)
    >>> app = Flask('app1')
    >>> app.config['SERVER_NAME'] = 'myapp.dev:5000'
    >>> app.add_url_rule("/x", endpoint="x")
    >>> with app.app_context():
    ...   current_app
    ...   g
    ...   request
    ...   session
    ...   url_for('x')
    ...
    <Flask 'app1'>
    <flask.g of 'app1'>
    <LocalProxy unbound>
    <LocalProxy unbound>
    'http://myapp.dev:5000/x'

Further, request contexts were made to implicitly create an application context.
Therefore, anything available in an application context is also available in a
request context::

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
