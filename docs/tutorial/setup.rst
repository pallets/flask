.. _tutorial-setup:

Step 2: Application Setup Code
==============================

Now that we have the schema in place we can create the application module.
Let's call it `flaskr.py` inside the `flaskr` folder.  For starters we
will add the imports and create the application object.  For small
applications it's a possibility to drop the configuration directly into
the module which we will be doing here.  However a cleaner solution would
be to create a separate `.ini` or `.py` file and load that or import the
values from there.

First we add the imports in `flaskr.py`::

    # all the imports
    import sqlite3
    from flask import Flask, request, session, g, redirect, url_for, abort, \
         render_template, flash

Next we can create our actual application and initialize it with the
config from the same file, in `flaskr.py`::

    # create our little application :)
    app = Flask(__name__)
    app.config.from_object(__name__)

    # Load default config and override config from an environment variable
    app.config.update(dict(
        DATABASE='/tmp/flaskr.db',
        DEBUG=True,
        SECRET_KEY='development key',
        USERNAME='admin',
        PASSWORD='default'
    ))
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

The :class:`~flask.Config` object works similar to a dictionary so we
can update it with new values.

.. admonition:: Windows

    If you are on Windows, replace `/tmp/flaskr.db` with a different writeable
    path of your choice, in the configuration and for the rest of this
    tutorial.

Usually, it is a good idea to load a separate, environment specific
configuration file.  Flask allows you to import multiple configurations and it 
will use the setting defined in the last import. This enables robust 
configuration setups.  :meth:`~flask.Config.from_envvar` can help achieve this. 
    
    app.config.from_envvar('FLASKR_SETTINGS', silent=True)

Simply define the environment variable :envvar:`FLASKR_SETTINGS` that points to 
a config file to be loaded.  The silent switch just tells Flask to not complain 
if no such environment key is set.

In addition to that you can use the :meth:`~flask.Config.from_object`
method on the config object and provide it with an import name of a
module.  Flask will the initialize the variable from that module.  Note
that in all cases only variable names that are uppercase are considered.

The ``SECRET_KEY`` is needed to keep the client-side sessions secure.
Choose that key wisely and as hard to guess and complex as possible.  The
debug flag enables or disables the interactive debugger.  *Never leave
debug mode activated in a production system*, because it will allow users to
execute code on the server!

We also add a method to easily connect to the database specified.  That
can be used to open a connection on request and also from the interactive
Python shell or a script.  This will come in handy later.  We create a
simple database connection through SQLite and then tell it to use the
:class:`sqlite3.Row` object to represent rows.  This allows us to treat
the rows as if they were dictionaries instead of tuples.

::

    def connect_db():
        """Connects to the specific database."""
        rv = sqlite3.connect(app.config['DATABASE'])
        rv.row_factory = sqlite3.Row
        return rv

Finally we just add a line to the bottom of the file that fires up the
server if we want to run that file as a standalone application::

    if __name__ == '__main__':
        app.run()

With that out of the way you should be able to start up the application
without problems.  Do this with the following command::

   python flaskr.py

You will see a message telling you that server has started along with
the address at which you can access it.

When you head over to the server in your browser you will get an 404
page not found error because we don't have any views yet.  But we will
focus on that a little later.  First we should get the database working.

.. admonition:: Externally Visible Server

   Want your server to be publicly available?  Check out the
   :ref:`externally visible server <public-server>` section for more
   information.

Continue with :ref:`tutorial-dbcon`.
