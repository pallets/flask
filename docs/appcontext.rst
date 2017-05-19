.. _app-context:

The Application Context
=======================

.. versionadded:: 0.9

One of the design ideas behind Flask is that there are two different
“states” in which code is executed.  The application setup state in which
the application implicitly is on the module level.  It starts when the
:class:`Flask` object is instantiated, and it implicitly ends when the
first request comes in.  While the application is in this state a few
assumptions are true:

-   the programmer can modify the application object safely.
-   no request handling happened so far
-   you have to have a reference to the application object in order to
    modify it, there is no magic proxy that can give you a reference to
    the application object you're currently creating or modifying.

In contrast, during request handling, a couple of other rules exist:

-   while a request is active, the context local objects
    (:data:`flask.request` and others) point to the current request.
-   any code can get hold of these objects at any time.

There is a third state which is sitting in between a little bit.
Sometimes you are dealing with an application in a way that is similar to
how you interact with applications during request handling; just that there
is no request active.  Consider, for instance, that you're sitting in an
interactive Python shell and interacting with the application, or a
command line application.

The application context is what powers the :data:`~flask.current_app`
context local.

Purpose of the Application Context
----------------------------------

The main reason for the application's context existence is that in the
past a bunch of functionality was attached to the request context for lack
of a better solution.  Since one of the pillars of Flask's design is that
you can have more than one application in the same Python process.

So how does the code find the “right” application?  In the past we
recommended passing applications around explicitly, but that caused issues
with libraries that were not designed with that in mind.

A common workaround for that problem was to use the
:data:`~flask.current_app` proxy later on, which was bound to the current
request's application reference.  Since creating such a request context is
an unnecessarily expensive operation in case there is no request around,
the application context was introduced.

Creating an Application Context
-------------------------------

There are two ways to make an application context.  The first one is
implicit: whenever a request context is pushed, an application context
will be created alongside if this is necessary.  As a result, you can
ignore the existence of the application context unless you need it.

The second way is the explicit way using the
:meth:`~flask.Flask.app_context` method::

    from flask import Flask, current_app

    app = Flask(__name__)
    with app.app_context():
        # within this block, current_app points to app.
        print current_app.name

The application context is also used by the :func:`~flask.url_for`
function in case a ``SERVER_NAME`` was configured.  This allows you to
generate URLs even in the absence of a request.

If no request context has been pushed and an application context has
not been explicitly set, a ``RuntimeError`` will be raised. ::

    RuntimeError: Working outside of application context.

Locality of the Context
-----------------------

The application context is created and destroyed as necessary.  It never
moves between threads and it will not be shared between requests.  As such
it is the perfect place to store database connection information and other
things.  The internal stack object is called :data:`flask._app_ctx_stack`.
Extensions are free to store additional information on the topmost level,
assuming they pick a sufficiently unique name and should put their
information there, instead of on the :data:`flask.g` object which is reserved
for user code.

For more information about that, see :ref:`extension-dev`.

Context Usage
-------------

The context is typically used to cache resources that need to be created
on a per-request or usage case.  For instance, database connections are
destined to go there.  When storing things on the application context
unique names should be chosen as this is a place that is shared between
Flask applications and extensions.

The most common usage is to split resource management into two parts:

1.  an implicit resource caching on the context.
2.  a context teardown based resource deallocation.

Generally there would be a ``get_X()`` function that creates resource
``X`` if it does not exist yet and otherwise returns the same resource,
and a ``teardown_X()`` function that is registered as teardown handler.

This is an example that connects to a database::

    import sqlite3
    from flask import g

    def get_db():
        db = getattr(g, '_database', None)
        if db is None:
            db = g._database = connect_to_database()
        return db

    @app.teardown_appcontext
    def teardown_db(exception):
        db = getattr(g, '_database', None)
        if db is not None:
            db.close()

The first time ``get_db()`` is called the connection will be established.
To make this implicit a :class:`~werkzeug.local.LocalProxy` can be used::

    from werkzeug.local import LocalProxy
    db = LocalProxy(get_db)

That way a user can directly access ``db`` which internally calls
``get_db()``.
