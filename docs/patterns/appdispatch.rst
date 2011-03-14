.. _app-dispatch:

Application Dispatching
=======================

Sometimes you might want to use multiple instances of the same application
with different configurations.  Assuming the application is created inside
a function and you can call that function to instanciate it, that is
really easy to implement.  In order to develop your application to support
creating new instances in functions have a look at the
:ref:`app-factories` pattern.


Dispatch by Subdomain
---------------------

A very common example would be creating applications per subdomain.  For
instance you configure your webserver to dispatch all requests for all
subdomains to your application and you then use the subdomain information
to create user-specific instances.

Once you have your server set up to listen on all subdomains you can use a
very simple WSGI application to do the dynamic application creation.

The code for the dispatching looks roughly like this:

.. sourcecode:: python

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
                    app = self.make_app(subdomain)
                    self.instances[subdomain] = app
                return app

        def make_app(self, subdomain):
            return self.create_app(subdomain)

        def __call__(self, environ, start_response):
            app = self.get_application(environ['HTTP_HOST'])
            return app(environ, start_response)


If you want to use it, you can do something like this:

.. sourcecode:: python

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
