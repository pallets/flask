.. _app-dispatch:

Application Dispatching
=======================

Application dispatching is the process of combining multiple Flask
applications on the WSGI level.  You can combine not only Flask
applications but any WSGI application.  This would allow you to run a
Django and a Flask application in the same interpreter side by side if
you want.  The usefulness of this depends on how the applications work
internally.

The fundamental difference from the :ref:`module approach
<larger-applications>` is that in this case you are running the same or
different Flask applications that are entirely isolated from each other.
They run different configurations and are dispatched on the WSGI level.


Working with this Document
--------------------------

Each of the techniques and examples below results in an ``application`` object
that can be run with any WSGI server.  For production, see :ref:`deployment`.
For development, Werkzeug provides a builtin server for development available
at :func:`werkzeug.serving.run_simple`::

    from werkzeug.serving import run_simple
    run_simple('localhost', 5000, application, use_reloader=True)

Note that :func:`run_simple <werkzeug.serving.run_simple>` is not intended for
use in production.  Use a :ref:`full-blown WSGI server <deployment>`.

In order to use the interactive debugger, debugging must be enabled both on
the application and the simple server. Here is the "hello world" example with
debugging and :func:`run_simple <werkzeug.serving.run_simple>`::

    from flask import Flask
    from werkzeug.serving import run_simple

    app = Flask(__name__)
    app.debug = True

    @app.route('/')
    def hello_world():
        return 'Hello World!'

    if __name__ == '__main__':
        run_simple('localhost', 5000, app,
                   use_reloader=True, use_debugger=True, use_evalex=True)


Combining Applications
----------------------

If you have entirely separated applications and you want them to work next
to each other in the same Python interpreter process you can take
advantage of the :class:`werkzeug.wsgi.DispatcherMiddleware`.  The idea
here is that each Flask application is a valid WSGI application and they
are combined by the dispatcher middleware into a larger one that is
dispatched based on prefix.

For example you could have your main application run on ``/`` and your
backend interface on ``/backend``::

    from werkzeug.wsgi import DispatcherMiddleware
    from frontend_app import application as frontend
    from backend_app import application as backend

    application = DispatcherMiddleware(frontend, {
        '/backend':     backend
    })


Dispatch by Subdomain
---------------------

Sometimes you might want to use multiple instances of the same application
with different configurations.  Assuming the application is created inside
a function and you can call that function to instantiate it, that is
really easy to implement.  In order to develop your application to support
creating new instances in functions have a look at the
:ref:`app-factories` pattern.

A very common example would be creating applications per subdomain.  For
instance you configure your webserver to dispatch all requests for all
subdomains to your application and you then use the subdomain information
to create user-specific instances.  Once you have your server set up to
listen on all subdomains you can use a very simple WSGI application to do
the dynamic application creation.

The perfect level for abstraction in that regard is the WSGI layer.  You
write your own WSGI application that looks at the request that comes and
delegates it to your Flask application.  If that application does not
exist yet, it is dynamically created and remembered::

    from threading import Lock

    class SubdomainDispatcher(object):

        def __init__(self, domain, create_app):
            self.domain = domain
            self.create_app = create_app
            self.lock = Lock()
            self.instances = {}

        def get_application(self, host):
            host = host.split(':')[0]
            assert host.endswith(self.domain), 'Configuration error'
            subdomain = host[:-len(self.domain)].rstrip('.')
            with self.lock:
                app = self.instances.get(subdomain)
                if app is None:
                    app = self.create_app(subdomain)
                    self.instances[subdomain] = app
                return app

        def __call__(self, environ, start_response):
            app = self.get_application(environ['HTTP_HOST'])
            return app(environ, start_response)


This dispatcher can then be used like this::

    from myapplication import create_app, get_user_for_subdomain
    from werkzeug.exceptions import NotFound

    def make_app(subdomain):
        user = get_user_for_subdomain(subdomain)
        if user is None:
            # if there is no user for that subdomain we still have
            # to return a WSGI application that handles that request.
            # We can then just return the NotFound() exception as
            # application which will render a default 404 page.
            # You might also redirect the user to the main page then
            return NotFound()

        # otherwise create the application for the specific user
        return create_app(user)

    application = SubdomainDispatcher('example.com', make_app)


Dispatch by Path
----------------

Dispatching by a path on the URL is very similar.  Instead of looking at
the ``Host`` header to figure out the subdomain one simply looks at the
request path up to the first slash::

    from threading import Lock
    from werkzeug.wsgi import pop_path_info, peek_path_info

    class PathDispatcher(object):

        def __init__(self, default_app, create_app):
            self.default_app = default_app
            self.create_app = create_app
            self.lock = Lock()
            self.instances = {}

        def get_application(self, prefix):
            with self.lock:
                app = self.instances.get(prefix)
                if app is None:
                    app = self.create_app(prefix)
                    if app is not None:
                        self.instances[prefix] = app
                return app

        def __call__(self, environ, start_response):
            app = self.get_application(peek_path_info(environ))
            if app is not None:
                pop_path_info(environ)
            else:
                app = self.default_app
            return app(environ, start_response)

The big difference between this and the subdomain one is that this one
falls back to another application if the creator function returns ``None``::

    from myapplication import create_app, default_app, get_user_for_prefix

    def make_app(prefix):
        user = get_user_for_prefix(prefix)
        if user is not None:
            return create_app(user)

    application = PathDispatcher(default_app, make_app)
