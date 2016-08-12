.. _tutorial-dbcon:

Step 4: Database Connections
----------------------------

You now have a function for establishing a database connection with
`connect_db`, but by itself, it is not particularly useful.  Creating and
closing database connections all the time is very inefficient, so you will
need to keep it around for longer.  Because database connections
encapsulate a transaction, you will need to make sure that only one
request at a time uses the connection. An elegant way to do this is by
utilizing the *application context*.

Flask provides two contexts: the *application context* and the
*request context*.  For the time being, all you have to know is that there
are special variables that use these.  For instance, the
:data:`~flask.request` variable is the request object associated with
the current request, whereas :data:`~flask.g` is a general purpose
variable associated with the current application context.  The tutorial
will cover some more details of this later on.

For the time being, all you have to know is that you can store information
safely on the :data:`~flask.g` object.

So when do you put it on there?  To do that you can make a helper
function.  The first time the function is called, it will create a database
connection for the current context, and successive calls will return the
already established connection::

    def get_db():
        """Opens a new database connection if there is none yet for the
        current application context.
        """
        if not hasattr(g, 'sqlite_db'):
            g.sqlite_db = connect_db()
        return g.sqlite_db

Now you know how to connect, but how can you properly disconnect?  For
that, Flask provides us with the :meth:`~flask.Flask.teardown_appcontext`
decorator.  It's executed every time the application context tears down::

    @app.teardown_appcontext
    def close_db(error):
        """Closes the database again at the end of the request."""
        if hasattr(g, 'sqlite_db'):
            g.sqlite_db.close()

Functions marked with :meth:`~flask.Flask.teardown_appcontext` are called
every time the app context tears down.  What does this mean?
Essentially, the app context is created before the request comes in and is
destroyed (torn down) whenever the request finishes.  A teardown can
happen because of two reasons: either everything went well (the error
parameter will be ``None``) or an exception happened, in which case the error
is passed to the teardown function.

Curious about what these contexts mean?  Have a look at the
:ref:`app-context` documentation to learn more.

Continue to :ref:`tutorial-dbinit`.

.. hint:: Where do I put this code?

   If you've been following along in this tutorial, you might be wondering
   where to put the code from this step and the next.  A logical place is to
   group these module-level functions together, and put your new
   ``get_db`` and ``close_db`` functions below your existing
   ``connect_db`` function (following the tutorial line-by-line).

   If you need a moment to find your bearings, take a look at how the `example
   source`_ is organized.  In Flask, you can put all of your application code
   into a single Python module.  You don't have to, and if your app :ref:`grows
   larger <larger-applications>`, it's a good idea not to.

.. _example source:
   https://github.com/pallets/flask/tree/master/examples/flaskr/
