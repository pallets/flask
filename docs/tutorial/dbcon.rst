.. _tutorial-dbcon:

Step 4: Request Database Connections
------------------------------------

Now we know how we can open database connections and use them for scripts,
but how can we elegantly do that for requests?  We will need the database
connection in all our functions so it makes sense to initialize them
before each request and shut them down afterwards.

Flask allows us to do that with the :meth:`~flask.Flask.before_request` and
:meth:`~flask.Flask.after_request` decorators::

    @app.before_request
    def before_request():
        g.db = connect_db()

    @app.after_request
    def after_request(response):
        g.db.close()
        return response

Functions marked with :meth:`~flask.Flask.before_request` are called before
a request and passed no arguments, functions marked with
:meth:`~flask.Flask.after_request` are called after a request and
passed the response that will be sent to the client.  They have to return
that response object or a different one.  In this case we just return it
unchanged.

We store our current database connection on the special :data:`~flask.g`
object that flask provides for us.  This object stores information for one
request only and is available from within each function.  Never store such
things on other objects because this would not work with threaded
environments.  That special :data:`~flask.g` object does some magic behind
the scenes to ensure it does the right thing.

Continue to :ref:`tutorial-views`.
