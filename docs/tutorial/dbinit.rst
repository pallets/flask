.. _tutorial-dbinit:

Step 4: Creating The Database
=============================

As outlined earlier, Flaskr is a database powered application, and more
precisely, it is an application powered by a relational database system.  Such
systems need a schema that tells them how to store that information. So
before starting the server for the first time it's important to create
that schema.

Such a schema can be created by piping the `schema.sql` file into the
`sqlite3` command as follows::

    sqlite3 /tmp/flaskr.db < schema.sql

The downside of this is that it requires the sqlite3 command to be
installed which is not necessarily the case on every system.  This also
require that we provide the path to the database  which can introduce
errors.  It's a good idea to add a function that initializes the database
for you to the application.

To do this we can create a function called `init_db` that initializes the
database.  Let me show you the code first.  Just add this function below
the `connect_db` function in `flaskr.py`::

    def init_db():
        with app.app_context():
            db = get_db()
            with app.open_resource('schema.sql', mode='r') as f:
                db.cursor().executescript(f.read())
            db.commit()

So what's happening here?  Remember how we learned last chapter that the
application context is created every time a request comes in?  Here we
don't have a request yet, so we need to create the application context by
hand.  Without an application context the :data:`~flask.g` object does not
know yet to which application it becomes as there could be more than one!

The ``with app.app_context()`` statement establishes the application
context for us.  In the body of the with statement the :data:`~flask.g`
object will be associated with ``app``.  At the end of the with statement
the association is released and all teardown functions are executed.  This
means that our database connection is disconnected after the commit.

The :func:`~flask.Flask.open_resource` method of the application object
is a convenient helper function that will open a resource that the
application provides.  This function opens a file from the resource
location (your `flaskr` folder) and allows you to read from it.  We are
using this here to execute a script on the database connection.

The connection object provided by SQLite can give us a cursor object.
On that cursor there is a method to execute a complete script.  Finally we
only have to commit the changes.  SQLite 3 and other transactional
databases will not commit unless you explicitly tell it to.

Now it is possible to create a database by starting up a Python shell and
importing and calling that function::

>>> from flaskr import init_db
>>> init_db()

.. admonition:: Troubleshooting

   If you get an exception later that a table cannot be found check that
   you did call the `init_db` function and that your table names are
   correct (singular vs. plural for example).

Continue with :ref:`tutorial-views`
