.. _sqlite3:

Using SQLite 3 with Flask
=========================

In Flask you can implement the opening of database connections at the
beginning of the request and closing at the end with the
:meth:`~flask.Flask.before_request` and :meth:`~flask.Flask.teardown_request`
decorators in combination with the special :class:`~flask.g` object.

So here is a simple example of how you can use SQLite 3 with Flask::

    import sqlite3
    from flask import g

    DATABASE = '/path/to/database.db'

    def connect_db():
        return sqlite3.connect(DATABASE)

    @app.before_request
    def before_request():
        g.db = connect_db()

    @app.teardown_request
    def teardown_request(exception):
        if hasattr(g, 'db'):
            g.db.close()

.. note::

   Please keep in mind that the teardown request functions are always
   executed, even if a before-request handler failed or was never
   executed.  Because of this we have to make sure here that the database
   is there before we close it.

Connect on Demand
-----------------

The downside of this approach is that this will only work if Flask
executed the before-request handlers for you.  If you are attempting to
use the database from a script or the interactive Python shell you would
have to do something like this::

    with app.test_request_context():
        app.preprocess_request()
        # now you can use the g.db object

In order to trigger the execution of the connection code.  You won't be
able to drop the dependency on the request context this way, but you could
make it so that the application connects when necessary::

    def get_connection():
        db = getattr(g, '_db', None)
        if db is None:
            db = g._db = connect_db()
        return db

Downside here is that you have to use ``db = get_connection()`` instead of
just being able to use ``g.db`` directly.

.. _easy-querying:

Easy Querying
-------------

Now in each request handling function you can access `g.db` to get the
current open database connection.  To simplify working with SQLite, a
helper function can be useful::

    def query_db(query, args=(), one=False):
        cur = g.db.execute(query, args)
        rv = [dict((cur.description[idx][0], value)
                   for idx, value in enumerate(row)) for row in cur.fetchall()]
        return (rv[0] if rv else None) if one else rv

This handy little function makes working with the database much more
pleasant than it is by just using the raw cursor and connection objects.

Here is how you can use it::

    for user in query_db('select * from users'):
        print user['username'], 'has the id', user['user_id']

Or if you just want a single result::

    user = query_db('select * from users where username = ?',
                    [the_username], one=True)
    if user is None:
        print 'No such user'
    else:
        print the_username, 'has the id', user['user_id']

To pass variable parts to the SQL statement, use a question mark in the
statement and pass in the arguments as a list.  Never directly add them to
the SQL statement with string formatting because this makes it possible
to attack the application using `SQL Injections
<http://en.wikipedia.org/wiki/SQL_injection>`_.

Initial Schemas
---------------

Relational databases need schemas, so applications often ship a
`schema.sql` file that creates the database.  It's a good idea to provide
a function that creates the database based on that schema.  This function
can do that for you::

    from contextlib import closing
    
    def init_db():
        with closing(connect_db()) as db:
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()

You can then create such a database from the python shell:

>>> from yourapplication import init_db
>>> init_db()
