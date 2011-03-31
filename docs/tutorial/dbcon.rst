.. _tutorial-dbcon:

Step 4: Request Database Connections
------------------------------------

Now we know how we can open database connections and use them for scripts,
but how can we elegantly do that for requests?  We will need the database
connection in all our functions so it makes sense to initialize them
before each request and shut them down afterwards.

Flask allows us to do that with the :meth:`~flask.Flask.before_request`,
:meth:`~flask.Flask.after_request` and :meth:`~flask.Flask.teardown_request`
decorators. In debug mode, if an error is raised,
:meth:`~flask.Flask.after_request` won't be run, and you'll have access to the
db connection in the interactive debugger::

    @app.before_request
    def before_request():
        g.db = connect_db()

    @app.after_request
    def after_request(response):
        g.db.close()
        return response

If you want to guarantee that the connection is always closed in debug mode, you
can close it in a function decorated with :meth:`~flask.Flask.teardown_request`::

    @app.before_request
    def before_request():
        g.db = connect_db()

    @app.teardown_request
    def teardown_request(exception):
        g.db.close()

Functions marked with :meth:`~flask.Flask.before_request` are called before
a request and passed no arguments.  Functions marked with
:meth:`~flask.Flask.after_request` are called after a request and
passed the response that will be sent to the client.  They have to return
that response object or a different one.  In this case we just return it
unchanged.

Functions marked with :meth:`~flask.Flask.teardown_request` get called after the
response has been constructed.  They are not allowed to modify the request, and
their return values are ignored.  If an exception occurred while the request was
being processed, it is passed to each function; otherwise, None is passed in.

We store our current database connection on the special :data:`~flask.g`
object that flask provides for us.  This object stores information for one
request only and is available from within each function.  Never store such
things on other objects because this would not work with threaded
environments.  That special :data:`~flask.g` object does some magic behind
the scenes to ensure it does the right thing.

Continue to :ref:`tutorial-views`.
