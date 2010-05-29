.. _tutorial-dbinit:

Step 3: Creating The Database
=============================

Flaskr is a database powered application as outlined earlier, and more
precisely, an application powered by a relational database system.  Such
systems need a schema that tells them how to store that information. So
before starting the server for the first time it's important to create
that schema.

Such a schema can be created by piping the `schema.sql` file into the
`sqlite3` command as follows::

    sqlite3 /tmp/flaskr.db < schema.sql

The downside of this is that it requires the sqlite3 command to be
installed which is not necessarily the case on every system.  Also one has
to provide the path to the database there which leaves some place for
errors.  It's a good idea to add a function that initializes the database
for you to the application.

If you want to do that, you first have to import the
:func:`contextlib.closing` function from the contextlib package.  If you
want to use Python 2.5 it's also necessary to enable the `with` statement
first (`__future__` imports must be the very first import)::

    from __future__ import with_statement
    from contextlib import closing

Next we can create a function called `init_db` that initializes the
database.  For this we can use the `connect_db` function we defined
earlier.  Just add that function below the `connect_db` function::

    def init_db():
        with closing(connect_db()) as db:
            with app.open_resource('schema.sql') as f:
                db.cursor().executescript(f.read())
            db.commit()

The :func:`~contextlib.closing` helper function allows us to keep a
connection open for the duration of the `with` block.  The
:func:`~flask.Flask.open_resource` method of the application object
supports that functionality out of the box, so it can be used in the
`with` block directly.  This function opens a file from the resource
location (your `flaskr` folder) and allows you to read from it.  We are
using this here to execute a script on the database connection.

When we connect to a database we get a connection object (here called
`db`) that can give us a cursor.  On that cursor there is a method to
execute a complete script.  Finally we only have to commit the changes.
SQLite 3 and other transactional databases will not commit unless you
explicitly tell it to.

Now it is possible to create a database by starting up a Python shell and
importing and calling that function::

>>> from flaskr import init_db
>>> init_db()

.. admonition:: Troubleshooting

   If you get an exception later that a table cannot be found check that
   you did call the `init_db` function and that your table names are
   correct (singular vs. plural for example).

Continue with :ref:`tutorial-dbcon`
