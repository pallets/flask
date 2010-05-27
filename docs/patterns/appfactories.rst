.. _app-factories:

Application Factories
=====================

If you are already using packages and modules for your application
(:ref:`packages`) there are couple of really nice ways to further improve
the experience.  A common pattern is creating the application object when
the module is imported.  But if you move the creation of this object,
into a function, you can then create multiple instances of this and later.

So why would you want to do this?

1.  Testing.  You can have instances of the application with different
    settings to test every case.
2.  Multiple instances.  Imagine you want to run different versions of the
    same application.  Of course you could have multiple instances with
    different configs set up in your webserver, but if you use factories,
    you can have multiple instances of the same application running in the
    same application process which can be handy.

So how would you then actually implement that?

Basic Factories
---------------

The idea is to set up the application in a function.  Like this::

    def create_app(config_filename):
        app = Flask(__name__)
        app.config.from_pyfile(config_filename)

        from yourapplication.views.admin import admin
        from yourapplication.views.frontend import frontend
        app.register_module(admin)
        app.register_module(frontend)

        return app

The downside is that you cannot use the application object in the modules
at import time.  You can however use it from within a request.  How do you
get access the application with the config?  Use
:data:`~flask.current_app`::

    from flask import current_app, Module, render_template
    admin = Module(__name__, url_prefix='/admin')

    @admin.route('/')
    def index():
        return render_template(current_app.config['INDEX_TEMPLATE'])

Here we look up the name of a template in the config.

Using Applications
------------------

So to use such an application you then have to create the application
first.  Here an example `run.py` file that runs such an application::

    from yourapplication import create_app
    app = create_app('/path/to/config.cfg')
    app.run()

Factory Improvements
--------------------

The factory function from above is not very clever so far, you can improve
it.  The following changes are straightforward and possible:

1.  make it possible to pass in configuration values for unittests so that
    you don't have to create config files on the filesystem
2.  call a function from a module when the application is setting up so
    that you have a place to modify attributes of the application (like
    hooking in before / after request handlers etc.)
3.  Add in WSGI middlewares when the application is creating if necessary.
