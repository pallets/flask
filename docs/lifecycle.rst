Application Structure and Lifecycle
===================================

Flask makes it pretty easy to write a web application. But there are quite a few
different parts to an application and to each request it handles. Knowing what happens
during application setup, serving, and handling requests will help you know what's
possible in Flask and how to structure your application.


Application Setup
-----------------

The first step in creating a Flask application is creating the application object. Each
Flask application is an instance of the :class:`.Flask` class, which collects all
configuration, extensions, and views.

.. code-block:: python

    from flask import Flask

    app = Flask(__name__)
    app.config.from_mapping(
        SECRET_KEY="dev",
    )
    app.config.from_prefixed_env()

    @app.route("/")
    def index():
        return "Hello, World!"

This is known as the "application setup phase", it's the code you write that's outside
any view functions or other handlers. It can be split up between different modules and
sub-packages, but all code that you want to be part of your application must be imported
in order for it to be registered.

All application setup must be completed before you start serving your application and
handling requests. This is because WSGI servers divide work between multiple workers, or
can be distributed across multiple machines. If the configuration changed in one worker,
there's no way for Flask to ensure consistency between other workers.

Flask tries to help developers catch some of these setup ordering issues by showing an
error if setup-related methods are called after requests are handled. In that case
you'll see this error:

    The setup method 'route' can no longer be called on the application. It has already
    handled its first request, any changes will not be applied consistently.
    Make sure all imports, decorators, functions, etc. needed to set up the application
    are done before running it.

However, it is not possible for Flask to detect all cases of out-of-order setup. In
general, don't do anything to modify the ``Flask`` app object and ``Blueprint`` objects
from within view functions that run during requests. This includes:

-   Adding routes, view functions, and other request handlers with ``@app.route``,
    ``@app.errorhandler``, ``@app.before_request``, etc.
-   Registering blueprints.
-   Loading configuration with ``app.config``.
-   Setting up the Jinja template environment with ``app.jinja_env``.
-   Setting a session interface, instead of the default itsdangerous cookie.
-   Setting a JSON provider with ``app.json``, instead of the default provider.
-   Creating and initializing Flask extensions.


Serving the Application
-----------------------

Flask is a WSGI application framework. The other half of WSGI is the WSGI server. During
development, Flask, through Werkzeug, provides a development WSGI server with the
``flask run`` CLI command. When you are done with development, use a production server
to serve your application, see :doc:`deploying/index`.

Regardless of what server you're using, it will follow the :pep:`3333` WSGI spec. The
WSGI server will be told how to access your Flask application object, which is the WSGI
application. Then it will start listening for HTTP requests, translate the request data
into a WSGI environ, and call the WSGI application with that data. The WSGI application
will return data that is translated into an HTTP response.

#.  Browser or other client makes HTTP request.
#.  WSGI server receives request.
#.  WSGI server converts HTTP data to WSGI ``environ`` dict.
#.  WSGI server calls WSGI application with the ``environ``.
#.  Flask, the WSGI application, does all its internal processing to route the request
    to a view function, handle errors, etc.
#.  Flask translates View function return into WSGI response data, passes it to WSGI
    server.
#.  WSGI server creates and send an HTTP response.
#.  Client receives the HTTP response.


Middleware
~~~~~~~~~~

The WSGI application above is a callable that behaves in a certain way. Middleware
is a WSGI application that wraps another WSGI application. It's a similar concept to
Python decorators. The outermost middleware will be called by the server. It can modify
the data passed to it, then call the WSGI application (or further middleware) that it
wraps, and so on. And it can take the return value of that call and modify it further.

From the WSGI server's perspective, there is one WSGI application, the one it calls
directly. Typically, Flask is the "real" application at the end of the chain of
middleware. But even Flask can call further WSGI applications, although that's an
advanced, uncommon use case.

A common middleware you'll see used with Flask is Werkzeug's
:class:`~werkzeug.middleware.proxy_fix.ProxyFix`, which modifies the request to look
like it came directly from a client even if it passed through HTTP proxies on the way.
There are other middleware that can handle serving static files, authentication, etc.


How a Request is Handled
------------------------

For us, the interesting part of the steps above is when Flask gets called by the WSGI
server (or middleware). At that point, it will do quite a lot to handle the request and
generate the response. At the most basic, it will match the URL to a view function, call
the view function, and pass the return value back to the server. But there are many more
parts that you can use to customize its behavior.

#.  WSGI server calls the Flask object, which calls :meth:`.Flask.wsgi_app`.
#.  A :class:`.RequestContext` object is created. This converts the WSGI ``environ``
    dict into a :class:`.Request` object. It also creates an :class:`AppContext` object.
#.  The :doc:`app context <appcontext>` is pushed, which makes :data:`.current_app` and
    :data:`.g` available.
#.  The :data:`.appcontext_pushed` signal is sent.
#.  The :doc:`request context <reqcontext>` is pushed, which makes :attr:`.request` and
    :class:`.session` available.
#.  The session is opened, loading any existing session data using the app's
    :attr:`~.Flask.session_interface`, an instance of :class:`.SessionInterface`.
#.  The URL is matched against the URL rules registered with the :meth:`~.Flask.route`
    decorator during application setup. If there is no match, the error - usually a 404,
    405, or redirect - is stored to be handled later.
#.  The :data:`.request_started` signal is sent.
#.  Any :meth:`~.Flask.url_value_preprocessor` decorated functions are called.
#.  Any :meth:`~.Flask.before_request` decorated functions are called. If any of
    these function returns a value it is treated as the response immediately.
#.  If the URL didn't match a route a few steps ago, that error is raised now.
#.  The :meth:`~.Flask.route` decorated view function associated with the matched URL
    is called and returns a value to be used as the response.
#.  If any step so far raised an exception, and there is an :meth:`~.Flask.errorhandler`
    decorated function that matches the exception class or HTTP error code, it is
    called to handle the error and return a response.
#.  Whatever returned a response value - a before request function, the view, or an
    error handler, that value is converted to a :class:`.Response` object.
#.  Any :func:`~.after_this_request` decorated functions are called, then cleared.
#.  Any :meth:`~.Flask.after_request` decorated functions are called, which can modify
    the response object.
#.  The session is saved, persisting any modified session data using the app's
    :attr:`~.Flask.session_interface`.
#.  The :data:`.request_finished` signal is sent.
#.  If any step so far raised an exception, and it was not handled by an error handler
    function, it is handled now. HTTP exceptions are treated as responses with their
    corresponding status code, other exceptions are converted to a generic 500 response.
    The :data:`.got_request_exception` signal is sent.
#.  The response object's status, headers, and body are returned to the WSGI server.
#.  Any :meth:`~.Flask.teardown_request` decorated functions are called.
#.  The :data:`.request_tearing_down` signal is sent.
#.  The request context is popped, :attr:`.request` and :class:`.session` are no longer
    available.
#.  Any :meth:`~.Flask.teardown_appcontext` decorated functions are called.
#.  The :data:`.appcontext_tearing_down` signal is sent.
#.  The app context is popped, :data:`.current_app` and :data:`.g` are no longer
    available.
#.  The :data:`.appcontext_popped` signal is sent.

There are even more decorators and customization points than this, but that aren't part
of every request lifecycle. They're more specific to certain things you might use during
a request, such as templates, building URLs, or handling JSON data. See the rest of this
documentation, as well as the :doc:`api` to explore further.
